import absl.flags
import datetime
import logging
import multiprocessing
import socket
import time

from concurrent import futures
from io import BytesIO

from meleeai.utils.message_type import MessageType
from meleeai.utils.controller_parser import ControllerParser
from meleeai.utils.slippi_parser import SlippiParser
from meleeai.utils.video_parser import VideoParser

from meleeai.framework.network.sender import NetworkSender
import json
import numpy as np
from copy import deepcopy
from meleeai.utils.util import getsize
from meleeai.memory import get_memory
from meleeai.utils.data_class import ControllerData, SlippiData


class NetworkReceiver():
    """Network Receiver"""
    def __init__(self):
        """Network receiver class for explicity set ports defined in flags.py.
        """
        # Global fields
        self._flags = absl.flags.FLAGS

        self._mp_dict        = {
            'controller': None,
            'slippi'    : None,
            #'video'     : None
        }

        self._func_dict         = {
            'controller': self._listen_controller,
            'slippi'    : self._listen_slippi,
            #'video'     : self._listen_video
        }

        self._namespace         = multiprocessing.Manager().Namespace()
        self._namespace.run     = True


    # Bypass Multiprocessing.Process for pickling
    def __getstate__(self):
        temporary_dictionary = self.__dict__.copy()
        temporary_dictionary['slippi_port'] = temporary_dictionary['_flags'].slippiport
        temporary_dictionary['controller_port'] = temporary_dictionary['_flags'].controllerport
        temporary_dictionary['video_port'] = temporary_dictionary['_flags'].videoport
        temporary_dictionary['receiver_buffer'] = temporary_dictionary['_flags'].receiverbuffer
        del temporary_dictionary['_mp_dict']
        del temporary_dictionary['_flags']
        return temporary_dictionary


    def __setstate__(self, state):
        self.__dict__.update(state)


    def _listen_controller(self, namespace):
        """Listens to the controller socket for any data sent from the Dolphin Emulator
        configured for said adresss & port in flags.
        :param namespace: Shared object by parent class.
        """
        controller_parser = ControllerParser()
        controller_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        controller_socket.bind(('', self.controller_port))
        controller_socket.settimeout(1)
        ns = NetworkSender()
        controller_memory_name = None
        memory = get_memory(self.receiver_buffer)
        while namespace.run:
            print('controller id ', id(memory))
            try:
                data_str, _         = controller_socket.recvfrom(2048)
                controller_data     = controller_parser.parse(data_str)
                if controller_data:
                    timestamp = float(f'{controller_data["timestamp_sec"]}.{controller_data["timestamp_micro"]}')
                    controller_memory_name, _ = memory.write_memory(ControllerData(MessageType.CONTROLLER, datetime.datetime.utcfromtimestamp(timestamp), controller_data))
                    if controller_data['device_number'] == 1:
                        ns.send(bytes(json.dumps(controller_data), encoding='utf-8'))
            except socket.timeout:
                logging.warning('Failed to receive any data from controller socket.')
            #except Exception as excp:
            #    logging.warning(f'Controller crashed. Error: {excp}.')
        controller_socket.close()


    def _listen_slippi(self, namespace):
        """Listens to the slippi socket for any data sent from the Dolphin Emulator
        configured for said adresss & port in flags.
        :param namespace: Shared object by parent class.
        """
        slippi_parser     = SlippiParser()
        slippi_socket     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        slippi_socket.bind(('', self.slippi_port))
        slippi_socket.settimeout(1)
        slippi_name = None
        memory = get_memory(self.receiver_buffer)
        while namespace.run:
            try:
                data_str, _         = slippi_socket.recvfrom(1024)
                events              = slippi_parser.parse_bin(BytesIO(data_str))
                if events:
                    for timestamp, event in events:
                        slippi_memory_name, _ = memory.write_memory(SlippiData(MessageType.SLIPPI, datetime.datetime.utcfromtimestamp(timestamp), event))
            except socket.timeout:
                logging.warning('Failed to receive any data from slippi socket.')
            except OSError as os_error:
                logging.warning(f'Slippi receiver pipeline has been closed. Error: {os_error}.')
            except Exception as excp:
                logging.warning(f'Slippi crashed. Error: {excp}.')
        slippi_socket.close()

    def _listen_video(self, namespace, receiver_list):
        pass
        """
        video_parser      = VideoParser()
        video_socket      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        video_socket.bind(('', self.videoport))
        video_socket.settimeout(1)
        while parent._namespace.run:
            try:
                data_str, _ = video_socket.recvfrom((2**16) - 1)
                if video_parser.update(data_str):
                    video_captures = video_parser.get_completed_images()
                    if video_captures and len(parent._receiver_list) <= self.receiver_buffer:
                        parent._receiver_list.append((MessageType.VIDEO, video_captures[0]))
            except socket.timeout:
                logging.warning('Failed to receive any data from video socket.')
            except OSError:
                logging.warning('Video receiver pipeline has been closed.')
        video_socket.close()
        """

    def collect(self):
        for name in self._func_dict:
            if not name in self._mp_dict or self._mp_dict[name] is None:
                self._mp_dict[name] = multiprocessing.Process(target=self._func_dict[name], args=(self._namespace,))
                self._mp_dict[name].start()
            if not self._mp_dict[name].is_alive():
                self._mp_dict[name].join()
                self._mp_dict[name] = None
            yield []

    def stop(self):
        logging.info('Stopped Network Receiver, awaiting thread completion.')
        self._namespace.run = False
        for mp_process in self._mp_dict.values():
            if mp_process and mp_process.is_alive():
                mp_process.join()
        logging.info('Successfully joined all threads, exiting Network Receiver.')