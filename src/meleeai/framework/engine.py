import datetime
import heapq
import logging
import os
import queue
import sys
import time
import threading

from multiprocessing import Process, Queue

from meleeai.framework.configuration import ConfigurationLoader
from meleeai.framework.display import StreamFrame, CommandType
from meleeai.framework.manager import Manager
from meleeai.framework.network.receiver import NetworkReceiver
from meleeai.utils.message_type import MessageType

# TODO: Engine should exist in its own thread, controlled by a constant tick rate; regardless of processing time.
class Engine:

    def __init__(self, config='alfred_config.yml', predict=False, display=False, train=False):
        # Global fields
        self._configuration = None
        self._predict = predict
        self._display = display
        self._train = train
        
        # Verify at least one functionality is active
        if not any([predict, display, train]):
            logging.error('No arguments provided, exiting.')
            exit(1)

        # Load the Alfred configuration
        self._configuration_loader = ConfigurationLoader(config_file=config)
        self._configuration = self._configuration_loader.load()

        # Objects used by the engine for network communication
        self._network_receiver  = NetworkReceiver(configured_ports=self._configuration['ports'])

        # Visual display
        self._display_queue_in  = Queue()
        self._display_queue_out = Queue()
        self._display_class     = StreamFrame(self._display_queue_in, self._display_queue_out)
        self._display_process   = None

        # Data Manager/Batcher & Algorithm
        self._data_manager = Manager()

        self._prediction_engine = None
        self._training_engine   = None

    def __enter__(self):
        # TODO: Place any code inside this body on object creation, works on calls to 'with'
        return self

    def __exit__(self, exec_type, exec_value, traceback):
        self._configuration_loader.save(configuration=self._configuration)

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

        self._network_receiver.stop()

    def main(self):
        if self._display:
            self._display_process = Process(target=self._display_class.run)
            self._display_process.start()
        from slippi.event import Frame, Start, End
        from collections import defaultdict
        counter = defaultdict(int)
        start = datetime.datetime.utcnow()
        while (datetime.datetime.utcnow() - start).total_seconds() < 5:
            for payload in self._network_receiver.collect():
                message_type, (timestamp, data) = payload
                # Display
                if message_type == MessageType.VIDEO:
                    if self._display_queue_in.qsize() <= self._configuration['display']['queue_size']:
                        self._display_queue_in.put_nowait((CommandType.VIDEO_UPDATE, data))

                if message_type == MessageType.SLIPPI:
                    if self._display_queue_in.qsize() <= self._configuration['display']['queue_size']:
                        self._display_queue_in.put_nowait((CommandType.SLIPPI_UPDATE, data))

                # Push the data retrieved to the manager
                self._data_manager.update(message_type=message_type, data=data, timestamp=timestamp)

            # Grab any available data from the manager
            retx = self._data_manager.retrieve()

            # Handle the _display_queue_out
            if self._display_queue_out.qsize() > 0:
                try:
                    payload = self._display_queue_out.get_nowait()
                    if payload[0] == CommandType.SHUTDOWN:
                        self._display = False
                except queue.Empty:
                    pass
        print(counter)
        if self._display:
            logging.info('SENDING shutdown command')
            self._display_queue_in.put_nowait((CommandType.SHUTDOWN, None))