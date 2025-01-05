from AbortWidget import AbortWidget
from InstallerResponse import InstallerResponse
from dialog import Dialog
import sys


class UsernameWidget:
    """
    A widget for prompting the user to input a username using a dialog box.

    Attributes:
        dialog (Dialog): The dialog object used to display the input box.
        config (dict): A dictionary containing configuration settings, including the initial username.

    Methods:
        show():
            Returns an InstallerResponse based on the user's action.
    """

    def __init__(self, dialog, config):
        """
        Initializes the UsernameWidget with the given dialog and configuration.

        Args:
            dialog: The dialog interface to be used by the widget.
            config: The configuration settings for the widget.
        """
        self.dialog = dialog
        self.config = config

    def show(self):
        """
        Prompts the user to input a username using a dialog box.

        This method displays an input box with a title "Select Username" and a pre-filled 
        initial value from the configuration. The dialog box has options for "Next" and "Back" 
        buttons, and does not allow cancellation.

        Returns:
            InstallerResponse: 
                - NEXT: If the user confirms the input.
                - PREVIOUS: If the user selects the "Back" button.
                - NONE: If the user aborts the input process.

        Exits:
            The program exits with status code 1 if the user aborts the input process and confirms the abort.
        """
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
            ret = AbortWidget(self.dialog)
            if ret == Dialog.OK:
                sys.exit(1)
            else:
                return InstallerResponse.NONE
