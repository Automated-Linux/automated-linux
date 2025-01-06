import os
from dialog import Dialog
import signal

from app.setup.config import ConfigManager
from app.setup.widgets.architecture import ArchitectureWidget
from app.setup.widgets.license import LicenseWidget
from app.setup.widgets.network import NetworkWidget
from app.setup.widgets.password import PasswordWidget
from app.setup.widgets.username import UsernameWidget


class Installer:
    """
    A class to handle the installation process of the Automated Linux Setup.

    Attributes:
        config_manager (ConfigManager): An instance of ConfigManager to handle configuration.
        config (dict): The configuration loaded from the ConfigManager.
        dialog (Dialog): An instance of Dialog to handle user interactions.
        width (int): The width of the dialog.
        height (int): The height of the dialog.

    Methods:
        license_agreement():
            Displays the license agreement to the user.

        setup_architeture():
            Displays the architecture setup dialog to the user.

        setup_username():
            Displays the username setup dialog to the user.

        setup_password():
            Displays the password setup dialog to the user.

        setup_network():
            Displays the network setup dialog to the user.

        run():
            Runs the installation process by executing a series of setup steps.
    """

    def __init__(self, columns: int, lines: int, config_file: str = "vars.yaml"):
        """
        Initializes the Installer class.

        Args:
            columns (int): The number of columns for the dialog interface.
            lines (int): The number of lines for the dialog interface.

        Attributes:
            config_manager (ConfigManager): An instance of ConfigManager to handle configuration.
            config (dict): The loaded configuration from ConfigManager.
            dialog (Dialog): An instance of Dialog for creating dialog interfaces.
            width (int): The width of the dialog interface.
            height (int): The height of the dialog interface.
        """
        self.config_manager = ConfigManager(config_path=config_file)
        self.config = self.config_manager.load_config()

        self.dialog = Dialog(dialog="dialog")
        self.dialog.set_background_title("Automated Linux Setup")
        self.dialog.add_persistent_args(
            ["--colors", "--insecure", "--no-collapse"])

        self.width = columns
        self.height = lines

        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def license_agreement(self):
        """
        Displays the license agreement widget.

        This method creates an instance of the LicenseWidget class with the dialog,
        width, and height attributes, and then shows the license agreement widget.

        Returns:
            bool: The result of showing the license agreement widget.
        """
        license_widget = LicenseWidget(self.dialog, self.width, self.height)
        return license_widget.show()

    def setup_architeture(self):
        """
        Sets up the architecture widget and displays it.

        This method initializes an instance of the ArchitectureWidget class
        with the dialog, width, height, and config attributes of the current
        instance. It then calls the show method on the architecture widget
        instance to display it.

        Returns:
            bool: The result of the architecture widget's show method, 
                  typically indicating whether the widget was displayed 
                  successfully.
        """
        architecture_widget = ArchitectureWidget(
            self.dialog, self.width, self.height, self.config)
        return architecture_widget.show()

    def setup_username(self):
        """
        Initializes and displays the UsernameWidget.

        This method creates an instance of the UsernameWidget using the dialog and
        config attributes, and then displays the widget.

        Returns:
            bool: The result of the UsernameWidget's show method, indicating
                  whether the username setup was successful.
        """
        username_widget = UsernameWidget(self.dialog, self.config)
        return username_widget.show()

    def setup_password(self):
        """
        Initializes and displays the password setup widget.

        This method creates an instance of the PasswordWidget class, passing the
        dialog and config attributes to its constructor. It then displays the
        password widget and returns the result of the show method.

        Returns:
            The result of the PasswordWidget's show method.
        """
        password_widget = PasswordWidget(self.dialog, self.config)
        return password_widget.show()

    def setup_network(self):
        """
        Initializes and displays the network setup widget.

        This method creates an instance of the NetworkWidget class, passing
        the dialog and config attributes to its constructor. It then calls
        the show method of the NetworkWidget instance to display the network
        setup interface.

        Returns:
            bool: The result of the NetworkWidget's show method, typically
              indicating whether the network setup was successful.
        """
        network_widget = NetworkWidget(
            self.dialog, self.config, self.width, self.height)
        return network_widget.show()

    def run(self):
        """
        Executes the installation process by running a series of setup steps.

        The method iterates through a list of configuration steps, executing each one in sequence.
        Each step is expected to return an integer that indicates the next step to execute.
        The process continues until all steps have been executed.

        Steps included in the process:
        - License agreement
        - Setup architecture
        - Setup username
        - Setup password
        - Setup network

        After all steps are completed, the configuration is saved using the config manager.
        """
        setup_config = [
            self.license_agreement,
            self.setup_architeture,
            self.setup_username,
            self.setup_password,
            self.setup_network,
        ]

        c_index = 0
        while c_index < len(setup_config):
            action = setup_config[c_index]()
            c_index += action

        self.config_manager.save_config(self.config)


def calculate_size():
    """
    Calculate the terminal size with adjusted dimensions.

    This function retrieves the current terminal size and adjusts the 
    columns to 90% of the original size and reduces the lines by 7.

    Returns:
        dict: A dictionary containing the adjusted 'columns' and 'lines' 
              of the terminal size.
    """
    size = os.get_terminal_size()
    return dict(columns=int(size.columns*90/100), lines=int(size.lines - 7))


def run_installer(columns: int, lines: int, config_file: str = "vars.yaml"):
    """
    Initializes and runs the Installer with the specified terminal dimensions.

    Args:
        columns (int): The number of columns in the terminal.
        lines (int): The number of lines in the terminal.
    """
    installer = Installer(columns, lines, config_file)
    installer.run()


if __name__ == "__main__":
    size = calculate_size()
    run_installer(size['columns'], size['lines'], 'vars.yaml')
