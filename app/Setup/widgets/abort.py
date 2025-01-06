import sys
from dialog import Dialog

from app.setup.response import InstallerResponse


class AbortWidget:
    """
    A widget to handle the abortion of an installation process.

    Attributes:
        dialog (Dialog): The dialog interface used to interact with the user.

    Methods:
        abort_installation():
            Prompts the user to confirm if they want to abort the installation.
            If the user confirms, the system exits with status code 1.
            Otherwise, it returns an InstallerResponse.NONE.
    """

    """
        Initializes the AbortWidget with a dialog interface and starts the abortion process.

        Args:
            dialog (Dialog): The dialog interface used to interact with the user.
        """

    """
        Prompts the user to confirm if they want to abort the installation.
        If the user confirms, the system exits with status code 1.
        Otherwise, it returns an InstallerResponse.NONE.
        """

    def __init__(self, dialog):
        """
        Initializes the AbortWidget with the given dialog and starts the abort installation process.

        Args:
            dialog: The dialog instance to be associated with the AbortWidget.
        """
        self.dialog = dialog
        self.abort_installation()

    def abort_installation(self):
        """
        Prompts the user with a confirmation dialog to abort the installation process.

        This method displays a dialog box asking the user if they are sure they want to abort the installation.
        If the user confirms (selects "Yes"), the system will exit with a status code of 1.
        If the user cancels (selects "No"), the method will return an InstallerResponse.NONE.

        Returns:
            InstallerResponse.NONE: If the user chooses not to abort the installation.
        """
        self.dialog.add_persistent_args(["--defaultno"])
        ret = self.dialog.yesno("\nAre you sure you want to abort the installation?",
                                width=50, height=8, title="Abort Installation")
        if ret == Dialog.OK:
            sys.exit(1)
        else:
            return InstallerResponse.NONE
