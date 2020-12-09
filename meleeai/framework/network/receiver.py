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
from multiprocessing.shared_memory import SharedMemory
import json
import numpy as np
from copy import deepcopy
from meleeai.utils.util import getsize

class NetworkReceiver():

    """
    TODO:
        - Test if shared memory works faster, looking for 0 latency performance from when it enters to being added
            * Appears to be the case, storing objects causes current unexplained crash
                > Assign to mem might be lost? Deepcopy didn't solve this
            * Analyze memory map, 8 bytes each but this indicates a pointer reference. how are integers handled?
                > Still being moved by 8 bytes inside the object array or 4 (np.int) bytes which struct('<I', self._shm_mem.buf.tobytes()) works
            * Can we calculate the size of the tuple (MESSAGETYPE, DATA) and determine size left to insert. There might be no assertions for this happening.
        > Exceeding was probably happening but mixing slippi and controller data together caused the issue
    """
    def __init__(self):
        """
        Network receiver class for explicity set ports defined in codebase.
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
        self._receiver_list     = multiprocessing.Manager().list()

        self.controller_arr     = np.ones(shape=(101), dtype=object)
        self._shm_mem_controller= SharedMemory(create=True, size=self.controller_arr.nbytes)

        controller_mem_arr = np.ndarray(self.controller_arr.shape, dtype=object, buffer=self._shm_mem_controller.buf)
        controller_mem_arr[:] = self.controller_arr[:]

        self.slippi_arr     = np.ones(shape=(101), dtype=object)
        self._shm_mem_slippi= SharedMemory(create=True, size=self.slippi_arr.nbytes)

        slippi_mem_arr = np.ndarray(self.slippi_arr.shape, dtype=object, buffer=self._shm_mem_slippi.buf)
        slippi_mem_arr[:] = self.slippi_arr[:]

        self.lock = multiprocessing.Lock()

        self._namespace.run     = True
        self._namespace.mem1    = self._shm_mem_controller.name
        self._namespace.mem2    = self._shm_mem_slippi.name

    def __del__(self):
        del self.shr_arr
        self._shm_mem.close()
        self._shm_mem.unlink()

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

    def __get_index(self, shm_array):
        """Gets the next index.
        :param shm_array: Array
        :return: Integer
        """
        return (shm_array[0] + 1) if shm_array[0] < (len(shm_array) - 1) else 1

    def _listen_controller(self, namespace, receiver_list):
        controller_parser = ControllerParser()
        controller_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        controller_socket.bind(('', self.controller_port))
        controller_socket.settimeout(1)
        ns = NetworkSender()
        existing_mem = SharedMemory(name=namespace.mem1)
        while namespace.run:
            try:
                data_str, _         = controller_socket.recvfrom(2048)
                controller_data     = controller_parser.parse(data_str)
                if controller_data and len(receiver_list) <= self.receiver_buffer:
                    timestamp = float(f'{controller_data["timestamp_sec"]}.{controller_data["timestamp_micro"]}')
                    #receiver_list.append((MessageType.CONTROLLER, (timestamp, controller_data)))
                    sh_mem_arr = np.ndarray(101, dtype=object, buffer=existing_mem.buf)
                    self.lock.acquire()
                    index = (sh_mem_arr[0] + 1) if sh_mem_arr[0] < (len(sh_mem_arr) - 1) else 1
                    x = getsize(deepcopy((MessageType.CONTROLLER, controller_data)))
                    print('controller ', x, getsize(existing_mem.buf))
                    sh_mem_arr[index] = deepcopy((MessageType.CONTROLLER, controller_data))
                    sh_mem_arr[0] = index
                    self.lock.release()
                    #print('controller RELEASE')
                    if controller_data['device_number'] == 1:
                        ns.send(bytes(json.dumps(controller_data), encoding='utf-8'))
            except socket.timeout:
                logging.warning('Failed to receive any data from controller socket.')
            except Exception as excp:
                logging.warning(f'Controller crashed. Error: {excp}.')
        existing_mem.close()
        controller_socket.close()


    def _listen_slippi(self, namespace, receiver_list):
        slippi_parser     = SlippiParser()
        slippi_socket     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        slippi_socket.bind(('', self.slippi_port))
        slippi_socket.settimeout(1)
        existing_mem = SharedMemory(name=namespace.mem2)
        while namespace.run:
            try:
                data_str, _         = slippi_socket.recvfrom(1024)
                events              = slippi_parser.parse_bin(BytesIO(data_str))
                if events and len(receiver_list) <= self.receiver_buffer:
                    #receiver_list.extend([(MessageType.SLIPPI, time_event) for time_event in events])
                    sh_mem_arr = np.ndarray(101, dtype=object, buffer=existing_mem.buf)
                    print('slippi acquire')
                    self.lock.acquire()
                    for event in events:
                        index = self.__get_index(sh_mem_arr)
                        # Ends early here
                        index = (sh_mem_arr[0] + 1) if sh_mem_arr[0] < (len(sh_mem_arr) - 1) else 1
                        x = getsize(deepcopy((MessageType.SLIPPI, event)))
                        print('slippi ', x, getsize(existing_mem.buf))
                        sh_mem_arr[index] = deepcopy((MessageType.SLIPPI, event))
                        sh_mem_arr[0] = index
                    self.lock.release()
                    print('slippi RELEASE')
            except socket.timeout:
                logging.warning('Failed to receive any data from slippi socket.')
            except OSError as os_error:
                logging.warning(f'Slippi receiver pipeline has been closed. Error: {os_error}.')
            except Exception as excp:
                logging.warning(f'Slippi crashed. Error: {excp}.')
        existing_mem.close()
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
                #logging.error(f'{not name in self._mp_dict}, {self._mp_dict[name] is None}')
                #if self._mp_dict[name]:
                #    logging.error(f'{not self._mp_dict[name].is_alive()}')
                #print(f'name {name}, namez {self._namespace.run}')
                self._mp_dict[name] = multiprocessing.Process(target=self._func_dict[name], args=(self._namespace, self._receiver_list, ))
                self._mp_dict[name].start()
            if not self._mp_dict[name].is_alive():
                self._mp_dict[name].join()
                self._mp_dict[name] = None
        while self._receiver_list:
            yield self._receiver_list.pop(0)

    def stop(self):
        logging.info('Stopped Network Receiver, awaiting thread completion.')
        self._namespace.run = False
        for mp_process in self._mp_dict.values():
            if mp_process and mp_process.is_alive():
                mp_process.join()
        logging.info('Successfully joined all threads, exiting Network Receiver.')