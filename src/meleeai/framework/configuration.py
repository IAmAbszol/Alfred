import logging
import os
import yaml

class ConfigurationLoader:

    _instance = None

    class _SingletonConfigurationLoader:

        def __init__(self, config_file):
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
                }
            }

    def __init__(self, config_file='alfred_config.yml'):
        if not ConfigurationLoader._instance:
            ConfigurationLoader._instance = ConfigurationLoader._SingletonConfigurationLoader(config_file)

    # TODO: Update _verify as new required items are added
    def _verify(self):
        ret = True
        ret &= 'display' in self._configuration.keys() and 'queue_size' in self._configuration['display'].keys()
        ret &= 'ports' in self._configuration.keys() and len(list(set(['controller', 'slippi', 'video']) & set(self._configuration['ports'].keys()))) == 3
        ret &= 'slippi' in self._configuration.keys() and bool(self._configuration['slippi'])
        return ret

    def get_config(self):
        return self._instance._configuration

    def save(self, configuration=None):
        with open(self._instance._config_file, 'w') as stream:
            yaml.dump(self._instance._configuration if not configuration else configuration, stream, default_flow_style=False)

    def load(self):
        if os.path.exists(self._instance._config_file) and os.path.isfile(self._instance._config_file):
            with open(self._instance._config_file, 'r') as stream:
                self._configuration = yaml.safe_load(stream)
        if self._verify():
            return self._configuration
        else:
            logging.error('Invalid configuration passed. Fresh config file might be required.')
            exit(1)