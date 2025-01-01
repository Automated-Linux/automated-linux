# automated-linux

Automated-Linux is an automation tool that simplifies the compilation and configuration of Linux systems from source code. It manages dependencies, optimizes the kernel, supports custom configurations, and provides an intuitive interface for a fast and efficient process.

## Create installation platform

To set up a Python virtual environment using Python 3.13 for installing Ansible, follow these steps:

1. **Install Python 3.13**: Ensure that Python 3.13 is installed on your system. You can download it from the official [Python website](https://www.python.org/downloads/).

2. **Create a virtual environment**: Use the `venv` module to create a virtual environment. This helps to manage dependencies and avoid conflicts with other projects.

   ```sh
   python3.13 -m venv venv
   ```

3. **Activate the virtual environment**: Activate the virtual environment to start using it.

   ```sh
   source venv/bin/activate
   ```

4. **Install Ansible**: With the virtual environment activated, install Ansible using `pip`.

   ```sh
   pip install ansible ansible-lint ansible-runner
   ```

5. **Verify the installation**: Check that Ansible is installed correctly by running:

   ```sh
   ansible --version
   ```

These steps will set up a Python 3.13 virtual environment and install Ansible, allowing you to manage your automation tasks efficiently.

For convenience you can use the following commands:

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Execute Runner

To start the Autometd-Linux tool, you need to execute the `run.py` script. Follow these steps:

1. Open a terminal.
2. Navigate to the directory where the `run.py` script is located.
3. Run the script using Python by executing the following command:

   ```sh
   source venv/bin/activate
   python3 run.py
   ```

This will initiate the Autometd-Linux tool.
