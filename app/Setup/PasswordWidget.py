from AbortWidget import AbortWidget
from InstallerResponse import InstallerResponse
from dialog import Dialog
import sys


class PasswordWidget:
    """
    A widget for handling password input and validation during an installation process.

    Attributes:
        dialog (Dialog): The dialog interface for displaying messages and input boxes.
        config (dict): Configuration dictionary to store the password.

    Methods:
        show():
            Displays the initial password input dialog and handles user responses.

        handle_password_input(password1):
            Validates the first password input and prompts for password confirmation.

        handle_password_confirmation(password1, password2):
            Confirms that the two password inputs match and updates the configuration.

        handle_abort():
            Handles the abort action by displaying an abort confirmation dialog.
    """

    def __init__(self, dialog, config):
        """
        Initializes the PasswordWidget with the given dialog and configuration.

        Args:
            dialog: The dialog interface to be used by the PasswordWidget.
            config: The configuration settings for the PasswordWidget.
        """
        self.dialog = dialog
        self.config = config

    def show(self):
        """
        Displays a password input dialog and handles the user's response.

        The dialog prompts the user to enter a password with options to proceed or go back.
        If the user selects "Next", the password input is processed.
        If the user selects "Back", the previous step is indicated.
        If the dialog is aborted, the abort handler is called.

        Returns:
            InstallerResponse: The result of handling the password input, 
                               indicating either the next step, the previous step, or an abort.
        """
        code, password1 = self.dialog.passwordbox("\n\\ZbPassword\\ZB",
                                                  width=40,
                                                  height=12,
                                                  title="Select Password",
                                                  init=self.config.get(
                                                      'PASSWORD', ''),
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
        """
        Handles the password input process.

        Args:
            password1 (str): The initial password input by the user.

        Returns:
            InstallerResponse: The response indicating the next step in the installation process.

        The function performs the following steps:
        1. Checks if the initial password is empty or less than 8 characters long. If so, it displays an error message and returns `InstallerResponse.NONE`.
        2. Prompts the user to repeat the password using a password box dialog.
        3. If the user confirms the password (Dialog.OK), it calls `handle_password_confirmation` to verify the passwords match.
        4. If the user chooses to go back (Dialog.EXTRA), it returns `InstallerResponse.PREVIOUS`.
        5. If the user cancels the operation, it calls `handle_abort` to handle the cancellation.
        """
        if password1 == "" or len(password1) < 8:
            self.dialog.msgbox(
                "Password must be at least 8 characters long. Please try again.", width=40, height=8, title="Error")
            return InstallerResponse.NONE

        code, password2 = self.dialog.passwordbox("\n\\ZbRepeat Password\\ZB",
                                                  width=40,
                                                  height=12,
                                                  title="Select Password",
                                                  init=self.config.get(
                                                      'PASSWORD', ''),
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
        """
        Handles the confirmation of two password inputs.

        Compares the two provided passwords and checks if they match. If they do not match,
        a message box is displayed with an error message. If they match, the password is
        stored in the configuration.

        Args:
            password1 (str): The first password input.
            password2 (str): The second password input.

        Returns:
            InstallerResponse: Returns InstallerResponse.NONE if the passwords do not match,
                               otherwise returns InstallerResponse.NEXT.
        """
        if password1 != password2:
            self.dialog.msgbox(
                "Passwords do not match. Please try again.", width=40, height=8, title="Error")
            return InstallerResponse.NONE
        else:
            self.config['PASSWORD'] = password1
            return InstallerResponse.NEXT

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
