from dialog import Dialog
import sys

from app.setup.response import InstallerResponse
from app.setup.widgets.abort import AbortWidget


class ArchitectureWidget:
    """
    A widget for selecting the architecture of the system.

    Attributes:
        dialog (Dialog): The dialog instance used for displaying the menu.
        width (int): The width of the dialog.
        height (int): The height of the dialog.
        config (dict): Configuration dictionary containing system settings.

    Methods:
        show():
            Displays the architecture selection menu and handles user input.
            Returns:
                InstallerResponse: The response based on user selection.
    """

    def __init__(self, dialog, width, height, config):
        """
        Initializes the ArchitectureWidget.

        Args:
            dialog (Dialog): The dialog associated with the widget.
            width (int): The width of the widget.
            height (int): The height of the widget.
            config (Config): The configuration settings for the widget.
        """
        self.dialog = dialog
        self.width = width
        self.height = height
        self.config = config

    def show(self):
        """
        Displays a dialog menu for selecting the architecture of the system.

        The method presents a menu with architecture choices (x86_64 and ARM64) and handles user input.
        Depending on the user's selection, it updates the configuration and returns the appropriate response.

        Returns:
            InstallerResponse: NEXT if the user selects an architecture, PREVIOUS if the user clicks the "Back" button,
                               or NONE if the user cancels the operation.
        """
        self.dialog.add_persistent_args(
            ["--default-item", self.config['ARCH']])
        code, tag = self.dialog.menu("Select the architecture of the system:",
                                     width=self.width,
                                     height=self.height,
                                     choices=[
                                         ("x86_64", "Intel/Amd x86 64bit"), ("ARM64", "arm64")],
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
            ret = AbortWidget(self.dialog)
            if ret == Dialog.OK:
                sys.exit(1)
            else:
                return InstallerResponse.NONE
