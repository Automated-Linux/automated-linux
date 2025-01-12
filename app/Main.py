from pyfiglet import Figlet
from app.config import APP_NAME
from app.runner import AnsibleRunner
from app.setup import Installer, calculate_size, run_installer
import sys


class Main():
    """
    Main class for the automated Linux application.
    Methods
    -------
    __init__():
        Initializes the Main class, sets up the Figlet title, and prints it.
    run():
        Calculates the size for the installer, runs the installer, and executes the AnsibleRunner.
        Handles FileNotFoundError if the .config file is not found.
    """

    def __init__(self, **kwargs):
        """
        Initializes the main application.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Attributes:
            ansible (AnsibleRunner): An instance of AnsibleRunner initialized with the provided arguments.

        Side Effects:
            Prints the application title in a stylized font to the console.
        """

        f = Figlet(font='standard', width=160)
        title = f.renderText(APP_NAME)
        print(f"\33[33m{title}\033[00m")
        self.ansible = AnsibleRunner(**kwargs)

    def run(self):
        """
        Executes the main application logic.

        This method performs the following steps:
        1. Calculates the size required for the installer.
        2. Runs the installer with the calculated size.
        3. Attempts to open and close the '.config' file.
        4. If the '.config' file is found, initializes and runs the AnsibleRunner.
        5. If the '.config' file is not found, writes an error message to stderr and exits the program with status code 1.

        Raises:
            FileNotFoundError: If the '.config' file is not found.
        """
        size = calculate_size()
        run_installer(size['columns'], size['lines'])
        try:
            with open('.config', 'r') as f:
                f.close()

                self.ansible.run()

        except FileNotFoundError:
            sys.stderr.write("unable to open .config file")
            sys.exit(1)
