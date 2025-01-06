class InstallerResponse:
    """
    A class to represent the response of an installer.

    Attributes:
        NEXT (int): Indicates the next step in the installation process.
        NONE (int): Indicates no action or a neutral response.
        PREVIOUS (int): Indicates the previous step in the installation process.
    """
    NEXT = 1
    NONE = 0
    PREVIOUS = -1
