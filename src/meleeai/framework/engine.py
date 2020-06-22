import datetime
import heapq
import logging
import os
import queue
import sys
import time
import threading

from multiprocessing import Process, Queue, Pipe

from meleeai.framework.configuration import ConfigurationLoader
from meleeai.framework.display import StreamFrame, CommandType
from meleeai.framework.network import NetworkCommunication
from meleeai.utils.message_type import MessageType

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
        self._network_pipe_out, self._network_pipe_in = Pipe()
        self._network_comms     = NetworkCommunication(self._network_pipe_in, inbound_ports=self._configuration['ports'], outbound_port=55082)

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
        self._configuration_loader.save(configuration=self._configuration)

        if self._display_process:
            self._display_process.join()

        # TODO: There seems to be some type of lag delay where if I were to sleep for x amount of time, it'd pass
        #       else WinApi error is thrown.
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
        if self._display:
            self._display_process = Process(target=self._display_class.run)
            self._display_process.start()

        start = datetime.datetime.utcnow()
        while (datetime.datetime.utcnow() - start).total_seconds() < 15:
            if self._network_pipe_out.poll():
                message_type, (_, data) = self._network_pipe_out.recv()
                if message_type == MessageType.VIDEO:
                    if self._display_queue_in.qsize() <= self._configuration['display']['queue_size']:
                        self._display_queue_in.put_nowait((CommandType.VIDEO_UPDATE, data))

                if message_type == MessageType.SLIPPI:
                    if self._display_queue_in.qsize() <= self._configuration['display']['queue_size']:
                        self._display_queue_in.put_nowait((CommandType.SLIPPI_UPDATE, data))

            # Handle the _display_queue_out
            if self._display_queue_out.qsize() > 0:
                try:
                    payload = self._display_queue_out.get_nowait()
                    if payload[0] == CommandType.SHUTDOWN:
                        self._display = False
                except queue.Empty:
                    pass
        if self._display:
            logging.info('SENDING shutdown command')
            self._display_queue_in.put_nowait((CommandType.SHUTDOWN, None))