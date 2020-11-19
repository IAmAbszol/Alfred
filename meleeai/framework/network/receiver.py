import absl.flags
import datetime
import logging
import multiprocessing
import socket
import time

from concurrent import futures
from io import BytesIO

from meleeai.utils.message_type import MessageType
from meleeai.utils.slippi_parser import SlippiParser
from meleeai.utils.video_parser import VideoParser


from slippi.event import Buttons, Frame, Start, End

class NetworkReceiver():

    def __init__(self):
        """
        Network receiver class for explicity set ports defined in codebase.
        """
        # Global fields
        self._flags = absl.flags.FLAGS

        self._mp_dict        = {
            'slippi'    : None,
            'video'     : None
        }

        self._func_dict         = {
            'slippi'    : self._listen_slippi,
            'video'     : self._listen_video
        }

        self._namespace         = multiprocessing.Manager().Namespace()
        self._namespace.run     = True
        self._receiver_list     = multiprocessing.Manager().list()
        self._run = True

        for name in self._func_dict:
            self._mp_dict[name] = multiprocessing.Process(target=self._func_dict[name], args=(self, ))


    def _listen_slippi(self, parent):
        slippi_parser     = SlippiParser()
        slippi_socket     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        slippi_socket.bind(('', self._flags.slippiport))
        slippi_socket.settimeout(1)
        while parent._namespace.run:
            try:
                data_str, _         = slippi_socket.recvfrom(1024)
                events              = slippi_parser.parse_bin(BytesIO(data_str))
                if events and len(parent._receiver_list) <= self._flags.receiverbuffer:
                    parent._receiver_list.extend([(MessageType.SLIPPI, time_event) for time_event in events])
            except socket.timeout:
                logging.warning('Failed to receive any data from slippi socket.')
            except OSError:
                logging.warning('Slippi receiver pipeline has been closed.')
            except Exception:
                logging.warning('Slippi crashed.')
        slippi_socket.close()

    def _listen_video(self, parent):
        video_parser      = VideoParser()
        video_socket      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        video_socket.bind(('', self._flags.videoport))
        video_socket.settimeout(1)
        while parent._namespace.run:
            try:
                data_str, _ = video_socket.recvfrom((2**16) - 1)
                if video_parser.update(data_str):
                    video_captures = video_parser.get_completed_images()
                    if video_captures and len(parent._receiver_list) <= self._flags.receiverbuffer:
                        parent._receiver_list.append((MessageType.VIDEO, video_captures[0]))
            except socket.timeout:
                logging.warning('Failed to receive any data from video socket.')
            except OSError:
                logging.warning('Video receiver pipeline has been closed.')
        video_socket.close()

    def collect(self):
        for name in self._func_dict:
            if self._namespace.run and not self._mp_dict[name].is_alive():
                self._mp_dict[name].start()
        while self._receiver_list:
            yield self._receiver_list.pop(0)

    def stop(self):
        logging.info('Stopped Network Receiver, awaiting thread completion.')
        self._namespace.run = False
        for mp_thread in self._mp_dict.values():
            mp_thread.join()
        logging.info('Successfully joined all threads, exiting Network Receiver.')