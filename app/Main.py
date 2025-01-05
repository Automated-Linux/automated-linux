from pyfiglet import Figlet
from .Config import APP_NAME
from .AnsibleRunner import AnsibleRunner
from .Setup import Installer
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

    def __init__(self):
        """
        Initializes the application by rendering the title using the Figlet library.

        This method sets up the initial state of the application by creating a Figlet
        object with a specified font and width. It then renders the application name
        as a stylized text and prints it to the console in yellow color.

        Attributes:
            None

        Parameters:
            None

        Returns:
            None
        """
        f = Figlet(font='standard', width=160)
        title = f.renderText(APP_NAME)
        print(f"\33[33m{title}\033[00m")

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
        size = Installer.calculate_size()
        Installer.run_installer(size['columns'], size['lines'])
        try:
            with open('.config', 'r') as f:
                f.close()

                ansible = AnsibleRunner()
                ansible.run()

        except FileNotFoundError:
            sys.stderr.write("unable to open .config file")
            sys.exit(1)
