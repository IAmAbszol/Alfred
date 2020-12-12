import absl.flags
import datetime
import logging
import os
import queue
import sys
import time
import threading

from multiprocessing import Process, Queue

from meleeai.framework.display import StreamFrame
from meleeai.framework.manager import Manager
from meleeai.framework.network.receiver import NetworkReceiver
from meleeai.memory import get_memory
from meleeai.utils.data_class import ControllerData, SlippiData
from meleeai.utils.message_type import MessageType

# TODO: Engine should exist in its own thread, controlled by a constant tick rate; regardless of processing time.
class Engine:
    """Engine"""
    def __init__(self):
        """Initializes Alfred's Engine
        """
        # Global fields
        self._flags = absl.flags.FLAGS
        self._display = self._flags.display
        self._train = self._flags.train

        # Objects used by the engine for network communication
        self._network_receiver  = NetworkReceiver()

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
        self._data_manager.close()

    def main(self):
        """Main instance for Alfred, used to communicate all processes together"""
        if self._display:
            self._display_process = Process(target=self._display_class.setup)
            self._display_process.start()

        start = datetime.datetime.utcnow()
        while True: #(datetime.datetime.utcnow() - start).total_seconds() < 30:
            display_queue_open = self._display_queue_in.qsize() <= self._flags.display_queuesize
            for payload in self._network_receiver.collect():
                lookup_ret = get_memory().lookup_object(ControllerData)
                #if lookup_ret:
                #    print(lookup_ret)
                #    exit(0)
                print('Engine id ', id(get_memory()))
                continue
                message_type, (timestamp, data) = payload
                # Display
                if self._display:
                    if message_type == MessageType.VIDEO:
                        if display_queue_open:
                            self._display_queue_in.put_nowait((MessageType.VIDEO, data))

                    if message_type == MessageType.SLIPPI:
                        if display_queue_open:
                            self._display_queue_in.put_nowait((MessageType.SLIPPI, data))

                # Push the data retrieved to the manager
                self._data_manager.update(message_type=message_type, data=data, timestamp=timestamp)

            self._data_manager.check_emulator_state()

            # Handle the _display_queue_out
            if self._display_queue_out.qsize() > 0:
                try:
                    payload = self._display_queue_out.get_nowait()
                    if payload[0] == MessageType.SHUTDOWN:
                        self._display = False
                except queue.Empty:
                    pass

        if self._display:
            logging.info('SENDING shutdown command')
            self._display_queue_in.put_nowait((MessageType.SHUTDOWN, None))
