import yaml


class ConfigManager:
    """
    A class to manage configuration settings for the automated Linux application.

    Methods
    -------
    load_config() -> dict:
        Loads the configuration from a YAML file. If the file is not found, returns a default configuration.

    save_config(config: dict):
        Saves the given configuration dictionary to a YAML file.
    """

    def __init__(self, config_path: str = 'vars.yml'):
        """
        Initializes the ConfigManager with the given configuration file path.

        Args:
            config_path (str): The path to the configuration file. Defaults to 'vars.yml'.
        """
        self.config_path = config_path

    def load_config(self) -> dict:
        """
        Loads the configuration from a YAML file specified by `self.config_path`.

        If the file is not found, returns a default configuration dictionary.

        Returns:
            dict: The configuration data loaded from the YAML file or the default configuration.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
        """

        try:
            with open(self.config_path, 'r') as infile:
                data = yaml.load(infile, Loader=yaml.FullLoader)
                infile.close()
        except FileNotFoundError:
            data = dict(
                ARCH='x86_64',
                HOSTNAME='automated-linux',
                USERNAME='automated',
                PASSWORD='automated',
                NETWORK=dict(
                    NETWORK_INTERFACE=None,
                    USE_DHCP=True,
                    NETWORK_IP_ADDRESS=None,
                    NETWORK_SUBNET_MASK=None,
                    NETWORK_GATEWAY=None,
                    NETWORK_DNS_PRIMARY=None,
                    NETWORK_DNS_SECONDARY=None,
                    DOMAIN=None,
                    SEARCH_DOMAIN=None
                )
            )
        return data

    def save_config(self, config: dict):
        """
        Save the given configuration dictionary to a YAML file.

        Args:
            config (dict): The configuration data to be saved.

        Raises:
            IOError: If the file cannot be opened or written to.
        """

        with open(self.config_path, 'w') as outfile:
            yaml.dump(config, outfile)
            outfile.close()
