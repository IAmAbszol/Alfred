import absl.flags
import datetime
import logging
import multiprocessing
import socket
import time

from io import BytesIO
from threading import Thread

from meleeai.memory import get_memory
from meleeai.utils.controller_parser import ControllerParser
from meleeai.utils.data_class import ControllerData, SlippiData, VideoData
from meleeai.utils.message_type import MessageType
from meleeai.utils.slippi_parser import SlippiParser
from meleeai.utils.video_parser import VideoParser


class NetworkReceiver():
    """Network Receiver"""
    def __init__(self):
        """Network receiver class for explicity set ports defined in flags.py.
        """
        # Initialize the memory singleton
        self._controller_memory_name, self._controller_circular_buffer = \
            get_memory().create(obj=ControllerData(MessageType.CONTROLLER, datetime.datetime.utcnow(), {}))
        self._slippi_memory_name, self._slippi_circular_buffer = \
            get_memory().create(obj=SlippiData(MessageType.CONTROLLER, datetime.datetime.utcnow(), {}))
        self._video_memory_name, self._video_circular_buffer = \
            get_memory().create(obj=VideoData(MessageType.VIDEO, datetime.datetime.utcnow(), {}))

        # Global fields
        self._flags             = absl.flags.FLAGS

        # key -> [function, circular_buffer, process (Defaulted to None)]
        self._active_functions  = {
            'controller': [self._listen_controller, self._controller_circular_buffer, None],
            'slippi': [self._listen_slippi, self._slippi_circular_buffer, None],
            'video': [self._listen_video, self._video_circular_buffer, None]
        }

        self._namespace         = multiprocessing.Manager().Namespace()
        self._namespace.run     = True

    # Bypass Multiprocessing.Process for pickling
    def __getstate__(self):
        temporary_dictionary = self.__dict__.copy()
        temporary_dictionary['slippi_port'] = temporary_dictionary['_flags'].slippiport
        temporary_dictionary['controller_port'] = temporary_dictionary['_flags'].controllerport
        temporary_dictionary['video_port'] = temporary_dictionary['_flags'].videoport
        del temporary_dictionary['_active_functions']
        del temporary_dictionary['_flags']
        return temporary_dictionary


    def __setstate__(self, state):
        self.__dict__.update(state)


    def _listen_controller(self):
        """Listens to the controller socket for any data sent from the Dolphin Emulator
        configured for said addresss & port in flags.
        """
        controller_parser = ControllerParser()
        controller_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        controller_socket.bind(('', self._flags.controllerport))
        controller_socket.settimeout(1)
        while self._namespace.run:
            try:
                data_str, _         = controller_socket.recvfrom(2048)
                controller_data     = controller_parser.parse(data_str)
                if controller_data:
                    timestamp = float(f'{controller_data["timestamp_sec"]}.{controller_data["timestamp_micro"]}')
                    self._controller_circular_buffer.write(ControllerData(MessageType.CONTROLLER, datetime.datetime.utcfromtimestamp(timestamp), controller_data))
            except socket.timeout:
                logging.warning('Failed to receive any data from controller socket.')
            except Exception as excp:
                logging.warning(f'Controller crashed. Error: {excp}.')
        controller_socket.close()


    def _listen_slippi(self):
        """Listens to the slippi socket for any data sent from the Dolphin Emulator
        configured for said addresss & port in flags.
        """
        slippi_parser     = SlippiParser()
        slippi_socket     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        slippi_socket.bind(('', self._flags.slippiport))
        slippi_socket.settimeout(1)
        while self._namespace.run:
            try:
                data_str, _         = slippi_socket.recvfrom(1024)
                events              = slippi_parser.parse_bin(BytesIO(data_str))
                if events:
                    for timestamp, event in events:
                        self._slippi_circular_buffer.write(SlippiData(MessageType.SLIPPI, datetime.datetime.utcfromtimestamp(timestamp), event))
            except socket.timeout:
                logging.warning('Failed to receive any data from slippi socket.')
            except OSError as os_error:
                logging.warning(f'Slippi receiver pipeline has been closed. Error: {os_error}.')
            except Exception as excp:
                logging.warning(f'Slippi crashed. Error: {excp}.')
        slippi_socket.close()

    def _listen_video(self):
        video_parser      = VideoParser()
        video_socket      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        video_socket.bind(('', self._flags.videoport))
        video_socket.settimeout(1)
        while self._namespace.run:
            try:
                data_str, _ = video_socket.recvfrom((2**16) - 1)
                if video_parser.update(data_str):
                    video_captures = video_parser.get_completed_images()
                    if video_captures:
                        # TODO: Try in-line lambda expression to convert x to datetime and leave y.
                        timestamp, data = video_captures[0]
                        self._video_circular_buffer.write(VideoData(MessageType.VIDEO, datetime.datetime.utcfromtimestamp(timestamp), data))
            except socket.timeout:
                logging.warning('Failed to receive any data from video socket.')
            except OSError:
                logging.warning('Video receiver pipeline has been closed.')
        video_socket.close()

    def collect(self):
        for name in self._active_functions:
            if self._active_functions[name][2] is None:
                self._active_functions[name][2] = Thread(target=self._active_functions[name][0])
                self._active_functions[name][2].start()
            if not self._active_functions[name][2].is_alive():
                self._active_functions[name][2].join()
                self._active_functions[name][2] = None
            try:
                yield self._active_functions[name][1].read()
            except IndexError as index_error:
                #logging.error(f'name {name} error {index_error}.')
                pass

    def stop(self):
        logging.info('Stopped Network Receiver, awaiting thread completion.')
        self._namespace.run = False
        for (_, _, process) in self._active_functions.values():
            if process and process.is_alive():
                process.join()
        logging.info('Successfully joined all threads, exiting Network Receiver.')