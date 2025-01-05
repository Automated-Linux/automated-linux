import sys
from dialog import Dialog
from InstallerResponse import InstallerResponse
from AbortWidget import AbortWidget


class LicenseWidget:
    """
    A widget to display and handle the license agreement dialog.
    Attributes:
        dialog (Dialog): The dialog object used to display the license agreement.
        width (int): The width of the license agreement dialog.
        height (int): The height of the license agreement dialog.
    Methods:
        __init__(dialog, width, height):
            Initializes the LicenseWidget with the given dialog, width, and height.
        show():
            Displays the license agreement dialog and handles user response.
            Returns InstallerResponse.NEXT if the user agrees to the license.
            Returns InstallerResponse.NONE if the user cancels the license agreement.
    """

    def __init__(self, dialog, width, height):
        """
        Initializes the LicenseWidget with the given dialog, width, and height.

        Args:
            dialog: The dialog instance to be associated with the LicenseWidget.
            width (int): The width of the LicenseWidget.
            height (int): The height of the LicenseWidget.
        """
        self.dialog = dialog
        self.width = width
        self.height = height

    def show(self):
        """
        Displays the license agreement dialog to the user.
        Reads the license text from 'installer/license.txt' and shows it in a dialog
        with options to accept or cancel. If the user cancels, an abort widget is shown
        and the program exits if the user confirms the abort.
        Returns:
            InstallerResponse: NEXT if the user accepts the license agreement,
                               NONE if the user cancels and does not confirm the abort.
        """
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
            ret = AbortWidget(self.dialog)
            if ret == Dialog.OK:
                sys.exit(1)
            else:
                return InstallerResponse.NONE

        return InstallerResponse.NEXT
