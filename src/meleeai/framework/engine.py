import datetime
import heapq
import logging
import os
import sys
import time
import threading
import yaml

from multiprocessing import Process, Queue, Pipe

from meleeai.framework.display import StreamFrame, CommandType
from meleeai.framework.network import NetworkCommunication
from meleeai.utils.message_type import MessageType

#NamespcaeProxy --> multiprocessing.manager.Namespace() = direct manipulation between processes

class ConfigurationLoader:
    # TODO: Update configuration as the program grows
    def __init__(self, config_file='alfred_config.yml'):
        self._config_file = config_file
        self.configuration = {
            'ports' : {
                'controller': 55071,
                'slippi': 55080,
                'video': 55081
            }
        }

    # TODO: Update _verify as new required items are added
    def _verify(self):
        ret = True
        ret &= 'ports' in self.configuration.keys() and len(list(set(['controller', 'slippi', 'video']) & set(self.configuration['ports'].keys()))) == 3
        return ret

    def save(self, configuration=None):
        with open(self._config_file, 'w') as stream:
            yaml.dump(self._configuration if not configuration else configuration, stream, default_flow_style=False)

    def load(self):
        if os.path.exists(self._config_file) and os.path.isfile(self._config_file):
            with open(self._config_file, 'r') as stream:
                self._configuration = yaml.safe_load(stream)
        if self._verify():
            return self.configuration
        else:
            logging.error('Invalid configuration passed. Fresh config file might be required.')
            exit(1)


class Engine:

    def __init__(self, config='alfred_config.yml', predict=False, display=False, train=False):
        # Global fields
        self.configuration = None
        self.predict = predict
        self.display = display
        self.train = train
        
        # Verify at least one functionality is active
        if not any([predict, display, train]):
            logging.error('No arguments provided, exiting.')
            exit(1)

        # Load the Alfred configuration
        self._configuration_loader = ConfigurationLoader(config_file=config)
        self.configuration = self._configuration_loader.load()

        # Objects used by the engine
        self._network_pipe_out, self._network_pipe_in = Pipe()
        self._network_comms     = NetworkCommunication(self._network_pipe_in, inbound_ports=self.configuration['ports'], outbound_port=55082)

        # Visual display
        self._display_queue_in  = Queue()
        self._display_queue_out = Queue()
        self._display_class     = StreamFrame(self._display_queue_in, self._display_queue_out)
        self._display_process   = None

        self._prediction_engine = None
        self._training_engine   = None

    def __enter__(self):
        self._network_comms.run()
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self._configuration_loader.save(configuration=self.configuration)
        if self._display_process:
            self._display_process.join()
        while not self._display_queue_in.empty():
            self._display_queue_in.get(timeout=.001)
        self._display_queue_in.close()
        self._display_queue_in.join_thread()
        while not self._display_queue_out.empty():
            self._display_queue_out.get(timeout=.001)
        self._display_queue_out.close()
        self._display_queue_out.join_thread()

        if self._network_pipe_out.poll():
            self._network_pipe_out.recv()
        self._network_pipe_out.close()

        self._network_comms.stop()

    def main(self):
        if self.display:
            self._display_process = Process(target=self._display_class.run)
            self._display_process.start()

        # TODO: Network is only sending video. Either split of sift through it.
        start = datetime.datetime.utcnow()
        while (datetime.datetime.utcnow() - start).total_seconds() < 3:
            if self._network_pipe_out.poll():
                _, (message_type, data) = self._network_pipe_out.recv()
                if message_type == MessageType.VIDEO and self.display:
                    if self._display_queue_in.qsize() <= 10:
                        self._display_queue_in.put_nowait((CommandType.UPDATE, data))
                if self._display_queue_out.qsize():
                    payload = self._display_queue_out.get_nowait()
                    if payload[0] == CommandType.SHUTDOWN:
                        self.display = False
        while self._display_queue_in.qsize() > 0:
            time.sleep(.01)
        if self.display:
            logging.info('SENDING shutdown command')
            self._display_queue_in.put_nowait((CommandType.SHUTDOWN, None))