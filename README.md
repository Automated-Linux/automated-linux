# automated-linux

Automated-Linux builds a full Linux system **from source** entirely through Ansible playbooks: it spins up a disposable Docker build container, cross-compiles a toolchain (binutils, GCC, glibc), natively builds the full userland (~60 packages) inside a chroot with **systemd as PID 1**, compiles a Linux kernel, and boots the result in QEMU — all with a handful of commands run from your Mac.

Target architecture: **aarch64** (matches Apple Silicon, so QEMU boots with native HVF acceleration).

Every push/PR touching `playbooks/` or `vars/` runs [`ansible-lint` + `ansible-playbook --syntax-check`](.github/workflows/lint.yml) — a fast, no-build correctness gate (the actual build takes hours and needs privileged Docker, so it isn't run in CI).

## How it works

The controller (Ansible, run from your Mac) drives a privileged Ubuntu Docker container entirely over the `community.docker` connection plugin — no manual `docker exec` needed anywhere in the pipeline, including the chroot phase (it runs `chroot` as a plain command through that same connection). The container mounts two disk images: `build-images/automated-linux-sources.img`, a plain loopback ext4 file, and `build-images/automated-linux-root.vmdk`, a Parallels/VMware-compatible vmdk attached via `qemu-nbd` (so the same file can be imported into Parallels Desktop or other non-QEMU tooling, not just booted with `-drive ...,format=raw`). These images **persist on your Mac's disk** independently of the container, so build progress survives container recreation — the container itself is fully disposable and gets deleted automatically at the end of a full run.

## Prerequisites

- **macOS on Apple Silicon** (for native QEMU acceleration via HVF; other hosts work but boot-test with software emulation only).
- **Docker Desktop**, with enough RAM allocated for a GCC bootstrap build. 10GB is *not* enough (causes OOM kills mid-build); **20GB+** recommended. Change it in Docker Desktop → Settings → Resources.
- **Homebrew** (for installing QEMU and `expect`).
- **Python 3.13** (for the Ansible controller venv).

## Setup

The project's own `venv/` (from the legacy `run.py` flow, see [Legacy entrypoint](#legacy-entrypoint-runpy) below) does not have the collections this pipeline needs. Create a dedicated controller venv:

```sh
python3.13 -m venv venv
source venv/bin/activate
pip install ansible-core requests
ansible-galaxy collection install community.docker community.general ansible.posix
```

Install QEMU and `expect` (used by the automated boot test):

```sh
brew install qemu expect
```

## Configuration

All tunables live in [`vars/automated-linux.yaml`](vars/automated-linux.yaml):

| Key | Purpose |
|---|---|
| `docker.container_name` | Name of the build container (default `automated-linux-build`) |
| `docker.cpuset_cpus` | CPUs pinned to the container. `"auto"` (default) computes `NCPU - 2` from Docker Desktop's actual current allocation (`docker.yaml` queries it via `docker_host_info`) — self-adjusts if you change Docker Desktop's own resource limits later. Set an explicit value (e.g. `"0-11"`) to override |
| `docker.memory` | Container memory limit. `"auto"` (default) computes `MemTotal - 2GB` the same way. Set an explicit value (e.g. `"18g"`) to override — either way, keep it below Docker Desktop's own memory allocation, not your Mac's total RAM; raising it here does nothing until Docker Desktop → Settings → Resources is given more to hand out |
| `root_image` / `sources_image` | Size and path of the two disk images (under `build-images/`, gitignored) |
| `kernel.version` / `kernel.url` | Kernel version to build |
| `qemu.memory` / `qemu.cpus` | VM resources for the boot test |
| `qemu.ssh_host_port` | Mac-side port forwarded to the VM's SSH (default `2222`) — see [Networking](#networking) |
| `packages` | Host build tools installed into the container via `apt` |

Source package versions/URLs are in [`packages.txt`](packages.txt) and hardcoded per-package in [`playbooks/packages/toolchain.yaml`](playbooks/packages/toolchain.yaml) (cross-toolchain) and [`playbooks/packages/build.yaml`](playbooks/packages/build.yaml) (native userland).

## Running the full build

One command, from the `playbooks/` directory, runs the entire pipeline end to end — creates the container, cross-compiles the toolchain, builds the kernel, builds the full userland inside a chroot (systemd as PID 1), builds an initramfs and installs GRUB, boots it in QEMU with an automated login+command verification, and deletes the container again:

```sh
source venv/bin/activate
cd playbooks
ansible-playbook automated-linux.yaml
```

Credentials for the built system: **`root` / `root`**. Boot goes through OVMF (UEFI firmware) → GRUB → kernel + initramfs → udev-driven root detection, the same chain real UEFI arm64 hardware uses (not a direct `-kernel` boot). Interactive boot command (printed at the end of the run too, with the exact Homebrew qemu path for `edk2-aarch64-code.fd` filled in):

```sh
cd build-images
qemu-system-aarch64 -M virt -cpu host -accel hvf -m 2048 \
  -drive if=pflash,format=raw,readonly=on,file="$(brew --prefix qemu)/share/qemu/edk2-aarch64-code.fd" \
  -drive if=pflash,format=raw,file=edk2-aarch64-vars.fd \
  -drive file=automated-linux-root.vmdk,if=none,id=hd0,format=vmdk \
  -device virtio-blk-device,drive=hd0 \
  -netdev user,id=net0,hostfwd=tcp::2222-:22 -device virtio-net-pci,netdev=net0 \
  -nographic
```

(the `-netdev`/`-device virtio-net-pci` pair gives the VM outbound networking and forwards Mac port 2222 to its SSH — see [Networking](#networking) below)

Exit the VM with `Ctrl-A` then `X`.

It is safe to re-run: image creation/formatting is skipped if the `.img` files already exist, and each package step skips extraction if its source directory is already present. A full run from nothing (toolchain + full userland + kernel) takes a few hours depending on your Mac's core count; a re-run that's mostly already built takes a couple of minutes (dominated by the boot test).

Flags, passed to the same command:

```sh
# skip the automated boot test, just get the container unmounted / print the command
ansible-playbook automated-linux.yaml -e qemu_run_test=false

# keep the container around afterwards instead of deleting it
ansible-playbook automated-linux.yaml -e qemu_cleanup_container=false
```

### Running a subset

[`automated-linux.yaml`](playbooks/automated-linux.yaml) is just an `import_playbook` chain — run any prefix of it directly if you don't need the whole thing, e.g. to only (re)build the toolchain and kernel without booting:

```sh
ansible-playbook docker.yaml prepare.yaml packages/toolchain.yaml kernel.yaml
```

[`site.yaml`](playbooks/site.yaml) is a saved alias for exactly that subset (toolchain + kernel, no userland/boot).

## Playbook reference

| Playbook | Runs on | Purpose |
|---|---|---|
| [`docker.yaml`](playbooks/docker.yaml) | Mac (localhost) | Creates/starts the privileged build container (with `--init`, see [Gotchas](#gotchas)), registers it in Ansible's inventory, bootstraps Python + sudo inside it |
| [`prepare.yaml`](playbooks/prepare.yaml) | Container | Installs host build packages, creates the `automated` user, creates/formats/mounts the two disk images |
| [`packages/toolchain.yaml`](playbooks/packages/toolchain.yaml) | Container | Cross-compiles binutils, GCC (2 passes), glibc, libstdc++, and core userland tools into the mounted root image |
| [`kernel.yaml`](playbooks/kernel.yaml) | Container | Builds the Linux kernel `Image` and installs modules into the root image |
| [`packages/build.yaml`](playbooks/packages/build.yaml) | Container | Orchestrator: mounts `/dev` `/proc` `/sys` `/run` into the target root, then imports ~60 modules under [`packages/build/`](playbooks/packages/build/) — one file per package, same pattern as `packages/toolchain/` — in dependency order, ending with **systemd built and wired up as `/sbin/init`** (PID 1, `multi-user.target` default, getty on both the serial console and `tty1`, D-Bus/logind/udev all active, networking via `systemd-networkd`+`systemd-resolved` — see below). Every package is built natively inside the chroot using the gcc/binutils/glibc that `packages/toolchain.yaml` already installed into `{{ root_image.mount_point }}/usr` |
| [`initramfs.yaml`](playbooks/initramfs.yaml) | Container | Builds `build-images/initramfs.img` from binaries already in the root image (util-linux, kmod, systemd-udevd) so the real root storage controller can be detected and its module loaded before root is mounted, then installs GRUB to the image's EFI System Partition — this is what makes the image boot on real UEFI arm64 hardware, not just via QEMU's `-kernel` shortcut |
| [`qemu.yaml`](playbooks/qemu.yaml) | Container, then Mac (localhost) | Repairs the root vmdk's filesystems (`e2fsck`/`fsck.vfat` via `qemu-nbd`, in the container) and disconnects it, then on the Mac: installs QEMU, deletes the build container, boots through OVMF+GRUB+initramfs and verifies the system |
| [`site.yaml`](playbooks/site.yaml) | Mac (localhost) | Chains `docker.yaml` + `prepare.yaml` + `packages/toolchain.yaml` + `kernel.yaml` (toolchain/kernel only, no userland or boot) |
| [`automated-linux.yaml`](playbooks/automated-linux.yaml) | Mac (localhost) | **Main entrypoint.** Chains all of the above, in order, for the complete build |

## Networking

Network configuration is native `systemd-networkd` (no netplan or NetworkManager — this isn't a Debian/Ubuntu base, and netplan is just a YAML-to-networkd/NetworkManager config generator anyway, so there's nothing it would add here). `packages/build/systemd.yaml` sets up:

- [`/etc/systemd/network/20-wired-dhcp.network`](playbooks/packages/build/systemd.yaml): `Match Name=!lo` / `Network DHCP=yes` — DHCP on every interface except loopback, so it works regardless of what the NIC gets named (`enp0s1` under QEMU's default naming).
- `systemd-resolved`, enabled, with `/etc/resolv.conf` symlinked to its `stub-resolv.conf` — DNS from the DHCP lease is picked up automatically.

To add a static IP, a different DHCP scope, or a second interface, add another `.network` file (or edit this one) in `/etc/systemd/network/` and `systemctl restart systemd-networkd` — see `man systemd.network`.

### SSH access from the Mac

The interactive boot commands printed by `qemu.yaml` (and `automated-linux.yaml`'s final run) include `-netdev user,hostfwd=tcp::2222-:22 -device virtio-net-pci` (port configurable via `qemu.ssh_host_port` in `vars/automated-linux.yaml`), so once the VM is up:

```sh
ssh -p 2222 root@localhost
```

This is QEMU user-mode (SLIRP) networking with a single forwarded port — the VM isn't reachable from other devices on your LAN, only from the Mac itself, but it needs no special privileges and just works. **True bridged networking (the VM getting its own LAN IP via `-netdev vmnet-bridged`) is not achievable without a paid Apple Developer ID Application certificate**: the `com.apple.vm.networking` entitlement it requires is one of Apple's *restricted* entitlements, and AMFI rejects any binary claiming it that isn't signed with a real Developer ID and (in practice) still needs Apple's own provisioning for that specific entitlement — a free "Apple Development" (Xcode) certificate isn't enough. If you attempt this yourself: re-signing Homebrew's QEMU with that entitlement and no matching profile doesn't just disable networking, it makes AMFI kill the binary outright, breaking QEMU entirely (`codesign --entitlements ... --force -s - $(brew --prefix qemu)/bin/qemu-system-aarch64` with only `com.apple.security.hypervisor` restores it).

## Gotchas

- **The build container runs `--privileged`.** A narrower `cap_add` set (`SYS_ADMIN`, `MKNOD`, `SYS_CHROOT`, `DAC_OVERRIDE`, `CHOWN`, `FOWNER`, `SETUID`, `SETGID`) plus a device-cgroup rule for loop devices (major `7`) was tried and fails at the very first loop-mount in `prepare.yaml` (`failed to setup loop device for ...automated-linux-root.img`) — Docker Desktop's VM needs more than that to let a container claim a fresh loop device via `mount -o loop`. Not worth re-attempting without a way to iterate against a real end-to-end run.
- **Default login is `root`/`root`, unchanged across every build.** This is acceptable here because the only network exposure is QEMU user-mode (SLIRP) with a single port forwarded to `localhost` on your own Mac (see [SSH access](#ssh-access-from-the-mac)) — nothing on your LAN or the internet can reach the VM. If you ever change the networking setup to expose the VM more broadly (bridged networking, a wider port-forward range, etc.), change this default first — the credential is intentionally weak for local-only convenience, not hardened for any kind of exposure.
- **Never leave the root vmdk connected via `qemu-nbd` in the container while QEMU is running against it.** Both write to the same file with independent caches, which corrupts the ext4 filesystem (bad block bitmap checksums). `qemu.yaml` guarantees this in two steps: a dedicated play repairs the filesystems (`fsck.vfat`/`e2fsck`) against the container's `qemu-nbd`-attached device and explicitly disconnects it (`qemu-nbd --disconnect`) when done, then a second play **deletes the build container outright** before booting (a stray `docker exec -it` shell with its cwd inside the mount can also hold it busy, so a soft `umount` alone isn't reliable). `docker.yaml` recreates the container from scratch on the next run.
- **If Docker Desktop restarts or the container is otherwise lost**, the disk images on `build-images/` are untouched — just re-run `ansible-playbook automated-linux.yaml` (or `site.yaml`) to recreate the container and pick up where you left off (the `automated` user and installed host packages get recreated automatically; already-built toolchain output is preserved on the images).
- **Re-running `packages/toolchain.yaml` after it already completed once used to fail with `Permission denied`.** Its last task (`Change ownership of toolchain directory`) intentionally `chown -R root:root`s `usr`/`lib`/`lib64`/`var`/`etc`/`bin`/`sbin`/`tools`, correct for a normal top-to-bottom run since nothing after it should write there as the `automated` user. A dedicated task at the start of `packages/toolchain.yaml` now resets ownership back to `automated_user` on every run, so this self-heals automatically. The same thing can still happen if you poke around inside the container manually as root (e.g. `docker exec ... mount -o loop ...` followed by ad hoc commands) — anything you touch outside of Ansible's `become_user: automated` tasks ends up owned by `root`. Fix that case with `docker exec automated-linux-build chown -R automated:automated /mnt/automated-linux/usr /mnt/automated-linux/lib /mnt/automated-linux/lib64 /mnt/automated-linux/var /mnt/automated-linux/etc /mnt/automated-linux/bin /mnt/automated-linux/sbin /mnt/automated-linux/tools` before re-running.
- **`build-images/` is gitignored — nothing in the repo backs it up.** If it ever goes missing unexpectedly, check `~/.Trash` before assuming it's gone; something in your workflow (Finder, an IDE action, a stray `rm`) may have trashed rather than deleted it. If it's truly gone, `ansible-playbook automated-linux.yaml` rebuilds everything from scratch (60–120 minutes).
- **25GB root image / 40GB sources image** are the defaults in `vars/automated-linux.yaml`; bump `root_image.size` / `sources_image.size` there before the first `prepare.yaml` run if you plan to add many more packages.
- **`automated-linux-root.vmdk` is GPT-partitioned (an EFI System Partition + an ext4 root partition), not a single whole-disk ext4 filesystem.** `prepare.yaml` only partitions/formats a freshly created image — if you already have a `build-images/automated-linux-root.img` from before this change, delete it (and `automated-linux-sources.img` is unaffected) and let the next full run recreate `automated-linux-root.vmdk` from scratch; the old whole-disk layout can't be mounted the new way.
- **The root image moved from a plain raw `.img` file to a vmdk (`automated-linux-root.vmdk`), attached via `qemu-nbd` instead of `losetup`.** This is what lets the same file be imported directly into Parallels Desktop (or other non-QEMU tooling) instead of only working with QEMU's `-drive ...,format=raw`. `losetup` cannot loop-mount a vmdk's own container format directly — only `qemu-nbd` understands it, exposing `/dev/nbd0` (`root_image.nbd_device` in `vars/automated-linux.yaml`) the same way `losetup -P` used to expose a loop device's partitions. If you have an old `automated-linux-root.img`, delete it — the pipeline no longer looks for it.
- **The graphical QEMU window uses `-device qemu-xhci -device usb-kbd` for keyboard input, not `virtio-keyboard-pci`.** The latter works but QEMU's Cocoa backend on macOS can't translate every physical key to a virtio keycode, spamming `virtio_input_handle_event: unmapped key: 0 [unmapped]` on the host and dropping those keystrokes; a plain USB keyboard (the kernel already has full USB/XHCI/HID support built in) doesn't have this problem.
- **systemd installs its libraries into `/usr/lib64`** (meson's platform auto-detection), while every other package in this build uses plain `/usr/lib`. `dbus.yaml` sets `PKG_CONFIG_PATH` to cover both so `pkg-config` finds `libsystemd`; keep this in mind if another package's build ever needs to link against something systemd provides.
- **Every `make -j` in the pipeline uses `nproc * 2`, not plain `nproc`.** `nproc` reflects `docker.cpuset_cpus`, so this deliberately oversubscribes the container's CPUs — normal practice for compiles, since no single job stays 100% CPU-bound the whole time (I/O, linking, etc.), and it noticeably shortens wall-clock time for CPU-heavy packages (GCC, glibc, the kernel). The tradeoff is peak memory: heavier parallel C++ compilation (GCC itself, systemd) means memory pressure scales with how many jobs are active at once, not just core count. `docker.cpuset_cpus`/`docker.memory` default to `"auto"` (see [Configuration](#configuration)), which reserves 2 CPUs and 2GB versus Docker Desktop's real current allocation specifically to keep this oversubscription safe; the OOM-kill failure mode already documented under [Prerequisites](#prerequisites) gets easier to hit if you override those to something more aggressive.
- **`ccache` wraps the host gcc/g++ used to bootstrap `binutils_stage1`/`gcc_stage1`** (everything from `glibc` onward uses the freshly built cross-toolchain in `tools/bin` instead, which isn't wrapped). None of the toolchain steps are guarded against already being built, so a full pipeline re-run always recompiles GCC from scratch — `CCACHE_DIR` lives on `build-images/.ccache` (gitignored, same persistence pattern as the two disk images) specifically so that cache survives the container being deleted and recreated between runs. First run populates the cache at full cost; subsequent full runs should see `gcc_stage1` compile noticeably faster. Not yet validated end-to-end with a real timed run — if a toolchain compile ever behaves strangely (miscompiled output, not just a slow build) and you want to rule ccache out, delete `build-images/.ccache` or temporarily remove `ccache` from `vars/automated-linux.yaml`'s `packages` list.
- **`expect` is not built.** Its 5.45.4 release predates Tcl 9's API (macros like `CONST`/`_ANSI_ARGS_`/`TCL_VARARGS` were removed) and needs real source patching, not just header shims, to compile against the Tcl 9.0.4 this build installs. It's skipped as non-essential — nothing else in the build or at boot depends on it, only `dejagnu`'s test runner and interactive use, and `dejagnu` itself doesn't need it to build.
- **The container runs with `--init` (tini as PID 1)** specifically so that the hundreds of short-lived `configure`/`conftest`/`gcc` processes spawned during the toolchain build get reaped instead of piling up as zombies. If you ever hand-roll a `docker run` for this container without `--init`, orphaned zombie processes will accumulate indefinitely (`sleep infinity` alone never calls `wait()`).
- **`kmod` must be built with `--with-zlib`.** All kernel modules ship gzip-compressed (`.ko.gz`, from `CONFIG_MODULE_COMPRESS_GZIP`), and without zlib support `depmod`/`modprobe` silently skip every module they cannot decompress — `modules.dep` ends up empty despite hundreds of `.ko.gz` files existing on disk, and `systemd-udevd` fails coldplug with `Failed to initialize libkmod context: Operation not supported`. `--with-openssl --with-xz --with-zstd` alone is not enough.
- **The initramfs has no `ldconfig`/dynamic-linker cache of its own.** util-linux is built with `--libdir=/usr/lib`, which the dynamic linker only resolves on the real root image because `util-linux.yaml` runs `ldconfig` there — the initramfs never does, so every dynamically-linked binary it carries (`mount`, `blkid`, ...) fails at runtime with `cannot open shared object file` unless `initramfs.yaml` generates its own `/etc/ld.so.cache` (`ldconfig -r`, run against the staging tree). Relatedly, `cp -a` on a `.so` symlink (e.g. `libmount.so.1 -> libmount.so.1.1.0`) copies the symlink but never its target — the initramfs needs `cp -aL` (dereference) or the copy is a dangling link that looks present but is not.
- **The initramfs `/init` script needs real coreutils, not just bash builtins.** `mount`, `blkid`, `switch_root`, `modprobe`/`depmod`/`insmod`, `mkdir`, `cat`, and `sleep` are all external binaries bash cannot substitute — missing any of them fails with `command not found` partway through boot with no root filesystem to log to.
- **`systemd-udevd --daemon` is a no-op on modern systemd (v261.1 here) — it no longer self-daemonizes.** Without a service manager already running (there is none yet in a bare initramfs), the process just stays in the foreground and the boot hangs forever waiting for it to exit. `templates/initramfs/init.sh.j2` backgrounds it explicitly with a plain `&` instead.
- **Root and `/boot/efi` filesystem drivers must be built directly into the kernel `Image`, not modules — for both mounts, not just root.** `/boot/efi` is a plain `fstab` entry resolved by systemd itself very early in real (post-`switch_root`) boot, with no explicit `modprobe` step the way `initramfs.yaml`'s `/init` handles the root filesystem — the kernel's own `request_module()` auto-load for an unknown fs type does not reliably fire in time here. `CONFIG_FAT_FS`/`CONFIG_VFAT_FS` need the same `--enable` treatment `kernel.yaml` already gives `CONFIG_EXT4_FS`. Separately, vfat's default codepage is `cp437` regardless of `CONFIG_NLS_DEFAULT` — without `CONFIG_NLS_CODEPAGE_437` built in too, mount still fails (`FAT-fs: codepage cp437 not found`) even with `FAT_FS`/`VFAT_FS` themselves built in. The kernel also needs `CONFIG_BINFMT_SCRIPT` built in (not a module) since `/init` itself is a `#!/bin/bash` script — without it the kernel cannot even exec PID 1 (`Failed to execute /init (error -8)`).
- **A stale `qemu-nbd` connection can survive an image file being deleted and recreated**, the same way a stale loop device could before the switch to vmdk/`qemu-nbd` — a leftover connection from a previous run can still be attached to an old, now-replaced backing file under the same device path, silently pointing `mount`/`mkfs` at garbage. `prepare.yaml` disconnects `root_image.nbd_device` whenever the image is freshly (re)created, before reconnecting it fresh.
- **`/dev/nbd0`'s partition device nodes (`nbd0p1`/`nbd0p2`) don't appear on their own.** Same root cause as the loop-device case below: there's no udev daemon in this bare container, so while `blockdev --rereadpt` makes the kernel aware of the partitions (visible under `/sys/class/block/nbd0/nbd0pN`), nothing creates the corresponding `/dev` special files — every playbook that needs them (`prepare.yaml`, `initramfs.yaml`, `qemu.yaml`) `mknod`s them by hand from the sysfs `dev` (major:minor) values first.
- **Homebrew's `qemu` bottle does not always ship `edk2-aarch64-vars.fd`** (dropped from the package as of 11.0.2, only `edk2-aarch64-code.fd` remains). `qemu.yaml` falls back to synthesizing a blank vars store (`dd if=/dev/zero`, sized to match `edk2-aarch64-code.fd`) when the template is missing — functionally identical to a fresh copy of the old template, since OVMF initializes a blank NVRAM store on first boot either way.
- **Filesystem repair (`e2fsck`/`fsck.vfat`) runs inside the build container against the `qemu-nbd`-attached device, not on the Mac host.** `hdiutil` (used back when the root image was a plain raw file) can attach a GPT-partitioned raw disk generically without understanding its filesystems, but it has no idea what a vmdk container even is — only `qemu-nbd` can expose the vmdk's actual partitions as block devices. This is why `qemu.yaml` now has an extra play that runs first, entirely inside the container, and disconnects `qemu-nbd` again before the container is deleted and QEMU takes exclusive ownership of the file.

## `run.py`

The original `run.py` / `app/` TUI installer (`python run.py -b <host>`) invokes `playbooks/automated-linux.yaml` too (via `ansible_runner`), so it now kicks off the same complete pipeline described above — but its own `venv/` (see `requirements.txt`) predates this pipeline and doesn't have `community.docker`/`community.general`/`ansible.posix` installed. Either install them there too, or just use `ansible-playbook automated-linux.yaml` directly from the venv set up in [Setup](#setup); that's the supported path.
