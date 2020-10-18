import logging
import os
import yaml

class ConfigurationLoader:
    """ConfigurationLoader"""
    _instance = None

    class _SingletonConfigurationLoader:
        """SingletonConfigurationLoader"""
        def __init__(self, config_file):
            """Initializes the singleton configuration class
            :param config_file: Configuration file handled by save/load functionality.
            """
            # TODO: Update configuration as the program grows
            self._config_file = config_file
            self._configuration = {
                'display': {
                    'queue_size': 10
                },
                'ports' : {
                    'controller': 55071,
                    'slippi': 55080,
                    'video': 55081
                },
                'slippi': {
                    # Start, Pre, Post, End
                    54: 418, 55: 64, 56: 52, 57: 2
                },
                'alfred': {
                    # (ms)
                    'tick_rate': .016,
                    'model': {
                        'alfred_port': 1,
                        'alfred_character': 'falcon',
                        'player_port': 4
                    }
                }
            }

    def __init__(self, config_file='alfred_config.yml'):
        """Initializes the ConfigurationLoader instance"""
        if not ConfigurationLoader._instance:
            ConfigurationLoader._instance = ConfigurationLoader._SingletonConfigurationLoader(config_file)

    # TODO: Update _verify as new required items are added
    def _verify(self):
        """Verifies the integrity of the configuration file passed through"""
        ret = True
        ret &= 'display' in self._instance._configuration.keys() and 'queue_size' in self._instance._configuration['display'].keys()
        ret &= 'ports' in self._instance._configuration.keys() and len(list(set(['controller', 'slippi', 'video']) & set(self._instance._configuration['ports'].keys()))) == 3
        ret &= 'slippi' in self._instance._configuration.keys() and bool(self._instance._configuration['slippi'])
        return ret

    def get_config(self):
        """Gets the current configuration of the system"""
        return self._instance._configuration

    def save(self, configuration=None):
        """Saves the configuration that's currently operating
        :param configuration: Configuration file.
        """
        with open(self._instance._config_file, 'w') as stream:
            yaml.dump(self._instance._configuration if not configuration else configuration, stream, default_flow_style=False)

    def load(self):
        """Loads the configuration into the system
        :return: Configuration instance or early exit (Not advised)
        """
        if os.path.exists(self._instance._config_file) and os.path.isfile(self._instance._config_file):
            with open(self._instance._config_file, 'r') as stream:
                self._instance._configuration = yaml.safe_load(stream)
        if self._verify():
            return self._instance._configuration
        else:
            logging.error('Invalid configuration passed. Fresh config file might be required.')
            exit(1)
