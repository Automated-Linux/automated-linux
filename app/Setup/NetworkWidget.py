from AbortWidget import AbortWidget
from InstallerResponse import InstallerResponse
import psutil
from dialog import Dialog
import sys


class NetworkWidget:
    """
    A widget for configuring network settings in an installer dialog.

    Attributes:
        dialog (Dialog): The dialog object used to display menus and input boxes.
        config (dict): The configuration dictionary to store network settings.
        width (int): The width of the dialog boxes.
        height (int): The height of the dialog boxes.

    Methods:
        __init__(dialog, config, width=40, height=12):
            Initializes the NetworkWidget with the given dialog, config, width, and height.

        show():
            Displays the network interface selection menu and handles user input.

        setup_static_network():
            Prompts the user for static network configuration details and updates the config.

        handle_network_input(prompt, config_key):
            Displays an input box for the given prompt and updates the config with the input value.

        setup_network_configuration():
            Displays the network configuration menu (DHCP or Static) and handles user input.

        handle_abort():
            Handles the abort action by displaying an abort confirmation dialog.
    """

    def __init__(self, dialog, config, width=40, height=12):
        """
        Initializes the NetworkWidget.

        Args:
            dialog (Dialog): The dialog instance to be used.
            config (Config): The configuration settings.
            width (int, optional): The width of the widget. Defaults to 40.
            height (int, optional): The height of the widget. Defaults to 12.
        """
        self.dialog = dialog
        self.config = config
        self.width = width
        self.height = height

    def show(self):
        """
        Displays a dialog menu to select a network interface.

        This method presents a dialog menu with a list of available network interfaces
        for the user to select. The selected network interface is then stored in the
        configuration. If the user chooses the "Back" option, the method returns an
        indication to go to the previous step. If the user cancels the dialog, the
        method handles the abort action.

        Returns:
            InstallerResponse.PREVIOUS: If the user selects the "Back" option.
            The result of `self.setup_network_configuration()`: If the user selects a network interface.
            The result of `self.handle_abort()`: If the user cancels the dialog.
        """
        while True:
            if self.config['NETWORK']['NETWORK_INTERFACE'] in psutil.net_if_addrs():
                self.dialog.add_persistent_args(
                    ["--default-item", self.config['NETWORK']['NETWORK_INTERFACE']])

            code, tag = self.dialog.menu("\n\\ZbNetwork Interface\\ZB",
                                         title="Select Network Interface",
                                         choices=[(iface, "")
                                                  for iface in psutil.net_if_addrs().keys()],
                                         extra_button=True,
                                         extra_label="Back",
                                         no_cancel=True,
                                         ok_label="Next"
                                         )

            if code == Dialog.OK:
                self.config['NETWORK']['NETWORK_INTERFACE'] = tag
            elif code == Dialog.EXTRA:
                return InstallerResponse.PREVIOUS
            else:
                return self.handle_abort()

            network_cofiguration = self.setup_network_configuration()
            if network_cofiguration == InstallerResponse.NEXT:
                return InstallerResponse.NEXT
            elif network_cofiguration == InstallerResponse.PREVIOUS:
                continue
            else:
                return network_cofiguration

    def setup_static_network(self):
        """
        Configures the static network settings by prompting the user for various network parameters.

        This method sequentially prompts the user to input the following network parameters:
        - IP Address
        - Subnet Mask
        - Gateway
        - Primary DNS
        - Secondary DNS
        - Domain
        - Search Domain

        If any of the inputs are invalid or not provided, the method returns `InstallerResponse.NONE`.
        If all inputs are valid, the method returns `InstallerResponse.NEXT`.

        Returns:
            InstallerResponse: `InstallerResponse.NONE` if any input is invalid, otherwise `InstallerResponse.NEXT`.
        """
        network_setup_config = [
            (self.handle_network_input, "IP Address", 'NETWORK_IP_ADDRESS'),
            (self.handle_network_input, "Subnet Mask", 'NETWORK_SUBNET_MASK'),
            (self.handle_network_input, "Gateway", 'NETWORK_GATEWAY'),
            (self.handle_network_input, "Primary DNS", 'NETWORK_DNS_PRIMARY'),
            (self.handle_network_input, "Secondary DNS", 'NETWORK_DNS_SECONDARY'),
            (self.handle_network_input, "Domain", 'DOMAIN'),
            (self.handle_network_input, "Search Domain", 'SEARCH_DOMAIN')
        ]

        c_index = 0
        while c_index < len(network_setup_config):
            if c_index < 0:
                return InstallerResponse.PREVIOUS

            func, prompt, config_key = network_setup_config[c_index]
            action = func(prompt, config_key)
            c_index += action

        return InstallerResponse.NEXT

    def handle_network_input(self, prompt, config_key):
        """
        Handles the network input from the user using a dialog input box.

        Parameters:
        prompt (str): The prompt message to display in the input box.
        config_key (str): The key to store the input value in the network configuration.

        Returns:
        bool: True if the user confirms the input, False if the user selects the "Back" button.
        """
        code, value = self.dialog.inputbox(f"\n\\Zb{prompt}\\ZB",
                                           title=f"Select {prompt}",
                                           extra_button=True,
                                           init=self.config['NETWORK'][config_key],
                                           extra_label="Back",
                                           no_cancel=True,
                                           ok_label="Next"
                                           )

        if code == Dialog.OK:
            self.config['NETWORK'][config_key] = value
            return InstallerResponse.NEXT
        elif code == Dialog.EXTRA:
            return InstallerResponse.PREVIOUS
        else:
            return self.handle_abort()

    def setup_network_configuration(self):
        """
        Configures the network settings for the system based on user input.

        This method presents a dialog to the user to select between DHCP and Static IP
        network configurations. Depending on the user's choice, it updates the network
        configuration in the `self.config` dictionary and proceeds to the next step in
        the installation process.

        Returns:
            InstallerResponse: The next step in the installation process. It can be
            `InstallerResponse.NEXT` if the user selects DHCP, the result of
            `self.setup_static_network()` if the user selects Static IP, or
            `InstallerResponse.PREVIOUS` if the user clicks the "Back" button.

        Raises:
            Any exceptions raised by the dialog methods or configuration updates.

        Dialog Options:
            - "DHCP": Use DHCP for network configuration.
            - "STATIC": Use Static IP for network configuration.
            - "Back": Return to the previous step in the installation process.
            - "Next": Proceed to the next step in the installation process.
        """
        while True:
            self.set_default_network_item()

            code, tag = self.dialog.menu("Select the network configuration of the system:",
                                         choices=[("DHCP", "Use DHCP"),
                                                  ("STATIC", "Static IP")],
                                         title="Select Network Configuration",
                                         extra_button=True,
                                         extra_label="Back",
                                         no_cancel=True,
                                         ok_label="Next"
                                         )

            if code == Dialog.OK:
                selection = self.handle_network_selection(tag)
                if selection == InstallerResponse.NEXT:
                    return InstallerResponse.NEXT
                elif selection == InstallerResponse.PREVIOUS:
                    continue
                else:
                    return selection
            elif code == Dialog.EXTRA:
                return InstallerResponse.PREVIOUS
            else:
                return self.handle_abort()

    def set_default_network_item(self):
        if self.config['NETWORK']['USE_DHCP']:
            self.dialog.add_persistent_args(["--default-item", "DHCP"])
        else:
            self.dialog.add_persistent_args(["--default-item", "STATIC"])

    def handle_network_selection(self, tag):
        self.config['NETWORK']['USE_DHCP'] = (tag == "DHCP")

        if self.config['NETWORK']['USE_DHCP']:
            return InstallerResponse.NEXT
        else:
            status = self.setup_static_network()
            if status == InstallerResponse.NEXT:
                return InstallerResponse.NEXT
            elif status == InstallerResponse.PREVIOUS:
                return InstallerResponse.PREVIOUS
            else:
                return status

    def handle_abort(self):
        """
        Handles the abort action by displaying an AbortWidget dialog.

        If the user confirms the abort action (Dialog.OK), the application will exit with status code 1.
        Otherwise, it returns InstallerResponse.NONE.

        Returns:
            InstallerResponse: The response indicating no action if the abort is not confirmed.
        """
        ret = AbortWidget(self.dialog)
        if ret == Dialog.OK:
            sys.exit(1)
        else:
            return InstallerResponse.NONE
