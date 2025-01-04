import os
import yaml
from dialog import Dialog
import signal
import sys

class InstallerResponse:
    NEXT = 1
    NONE = 0
    PREVIOUS = -1

class Installer:

    def __init__(self, columns: int, lines: int):
        self.config = self.load_config()

        self.dialog = Dialog(dialog="dialog")
        self.dialog.set_background_title("Automated Linux Setup")
        self.dialog.add_persistent_args(["--colors", "--insecure", "--no-collapse"])

        self.width = columns
        self.height = lines

        signal.signal(signal.SIGINT, signal.SIG_IGN)
        
    def load_config(self) -> dict:
        try:
            with open('vars.yml', 'r') as infile:
                data = yaml.load(infile, Loader=yaml.FullLoader)
                infile.close()
        except FileNotFoundError:
            data = dict(
                ARCH = 'x86_64',
                HOSTNAME = 'automated-linux',
                USERNAME = 'automated',
                PASSWORD = 'automated',
                NETWORK = dict(
                    USE_DHCP = True,
                    NETWORK_IP_ADDRESS = None,
                    NETWORK_SUBNET_MASK = None,
                    NETWORK_GATEWAY = None,
                    NETWORK_DNS_PRIMARY = None,
                    NETWORK_DNS_SECONDARY = None,
                    DOMAIN = None,
                    SEARCH_DOMAIN = None
                )
            )
        return data

    def save_config(self):
        with open('vars.yml', 'w') as outfile:
            yaml.dump(self.config, outfile)
            outfile.close()

    def abort_installation(self):
        self.dialog.add_persistent_args(["--defaultno"])
        ret = self.dialog.yesno("\nAre you sure you want to abort the installation?", width=50, height=8, title="Abort Installation")
        if ret == Dialog.OK:
            sys.exit(1)
        else:
            return InstallerResponse.NONE

    def license_agreement(self):
        license_text = ""

        with open('installer/license.txt', 'r') as infile:
            license_text = infile.read()
            infile.close()

        self.dialog.add_persistent_args(["--no-nl-expand", '--colors'])
        accept = self.dialog.yesno(license_text, 
            width=self.width, 
            height=self.height, 
            title="License Agreement",
            yes_label="I agree",
            no_label="Cancel")

        if accept in [Dialog.CANCEL, Dialog.ESC]:
            ret = self.abort_installation()
            if ret == Dialog.OK:
                sys.exit(1)
            else:
                return InstallerResponse.NONE
       
        return InstallerResponse.NEXT
    
    def set_architeture(self):
        self.dialog.add_persistent_args(["--default-item", self.config['ARCH']])
        code, tag = self.dialog.menu("Select the architecture of the system:", 
            width=self.width, 
            height=self.height, 
            choices=[("x86_64", "Intel/Amd x86 64bit"), ("ARM64", "arm64")],
            title="Select Architecture",
            extra_button=True,
            extra_label="Back",
            no_cancel=True,
            ok_label="Next"
        )

        if code == Dialog.OK:
            self.config['ARCH'] = tag
            return InstallerResponse.NEXT
        elif code == Dialog.EXTRA:
            return InstallerResponse.PREVIOUS
        else:
            ret = self.abort_installation()
            if ret == Dialog.OK:
                sys.exit(1)
            else:
                return InstallerResponse.NONE

    def set_username(self):
        code, tag = self.dialog.inputbox("\n\\ZbUsername\\ZB", 
            width=40, 
            height=12, 
            title="Select Username",
            init=self.config['USERNAME'],
            extra_button=True,
            extra_label="Back",
            no_cancel=True,
            ok_label="Next"
        )

        if code == Dialog.OK:
            self.config['USERNAME'] = tag
            return InstallerResponse.NEXT
        elif code == Dialog.EXTRA:
            return InstallerResponse.PREVIOUS
        else:
            ret = self.abort_installation()
            if ret == Dialog.OK:
                sys.exit(1)
            else:
                return InstallerResponse.NONE

    def set_password(self):
        code, password1 = self.dialog.passwordbox("\n\\ZbPassword\\ZB", 
            width=40, 
            height=12, 
            title="Select Password",
            extra_button=True,
            extra_label="Back",
            no_cancel=True,
            ok_label="Next",
            insecure=True
        )
        
        if code == Dialog.OK:
            return self.handle_password_input(password1)
        elif code == Dialog.EXTRA:
            return InstallerResponse.PREVIOUS
        else:
            return self.handle_abort()

    def handle_password_input(self, password1):
        if password1 == "" or len(password1) < 8:
            self.dialog.msgbox("Password must be at least 8 characters long. Please try again.", width=40, height=8, title="Error")
            return InstallerResponse.NONE
        
        code, password2 = self.dialog.passwordbox("\n\\ZbRepeat Password\\ZB", 
            width=40, 
            height=12, 
            title="Select Password",
            extra_button=True,
            extra_label="Back",
            no_cancel=True,
            ok_label="Next",
            insecure=True
        )
        
        if code == Dialog.OK:
            return self.handle_password_confirmation(password1, password2)
        elif code == Dialog.EXTRA:
            return InstallerResponse.PREVIOUS
        else:
            return self.handle_abort()

    def handle_password_confirmation(self, password1, password2):
        if password1 != password2:
            self.dialog.msgbox("Passwords do not match. Please try again.", width=40, height=8, title="Error")
            return self.NONE
        else:
            self.config['PASSWORD'] = password1
            return InstallerResponse.NEXT

    def handle_abort(self):
        ret = self.abort_installation()
        if ret == Dialog.OK:
            sys.exit(1)
        else:
            return InstallerResponse.NONE

    def run(self):
        run_config = [
            self.license_agreement,
            self.set_architeture,
            self.set_username,
            self.set_password
        ]

        c_index= 0
        while c_index < len(run_config):
            action = run_config[c_index]()
            c_index += action

        self.save_config()

def calculate_size():
    size = os.get_terminal_size()
    return dict(columns=int(size.columns*90/100), lines=int(size.lines - 7))

def run_installer(columns: int, lines: int):
    installer = Installer(columns, lines)
    installer.run()

if __name__ == "__main__":
    size = calculate_size()
    run_installer(size['columns'], size['lines'])

