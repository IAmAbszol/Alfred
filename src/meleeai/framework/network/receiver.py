import logging
import socket
import time
import threading

from concurrent import futures
from io import BytesIO

from meleeai.utils.message_type import MessageType
from meleeai.utils.video_parser import VideoParser
from meleeai.utils.slippi_parser import SlippiParser

class NetworkReceiver():

    def __init__(self, configured_ports):
        """
        Network receiver class for explicity set ports defined in codebase.
        :param configured_ports: Dictionary from loaded config
        """
        # Setup ThreadExecutor
        self._executor = futures.ThreadPoolExecutor(max_workers=2)
        
        # Setup slippi
        self._slippi_parser     = SlippiParser()
        self._slippi_socket     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._slippi_socket.bind(('localhost', configured_ports['slippi']))
        self._slippi_socket.settimeout(1)

        # Setup video port
        self._video_parser      = VideoParser()
        self._video_socket      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._video_socket.bind(('localhost', configured_ports['video']))
        self._video_socket.settimeout(1)

        self._async_dict        = {
            'slippi'    : None,
            'video'     : None
        }

        self._func_dict         = {
            'slippi'    : self._listen_slippi,
            'video'     : self._listen_video
        }

    def _listen_slippi(self):
        try:
            data_str, _ = self._slippi_socket.recvfrom(512)
            event       = self._slippi_parser.parse_bin(BytesIO(data_str[4:]))
            if event:
                return (MessageType.SLIPPI, (_, event))
        except socket.timeout:
            logging.warning('Failed to receive any data from slippi socket.')        
        except OSError:
            logging.warning('Slippi receiver pipeline has been closed')

    def _listen_video(self):
        try:
            data_str, _ = self._video_socket.recvfrom((2**16) - 1)
            if self._video_parser.update(data_str):
                video_captures = self._video_parser.get_completed_images()
                if video_captures:
                    return (MessageType.VIDEO, video_captures[0])
        except socket.timeout:
            logging.warning('Failed to receive any data from video socket.')    
        except OSError:
            logging.warning('Video receiver pipeline has been closed')

    def collect(self):
        for name, fut in self._async_dict.items():
            if fut and fut.done():
                if fut.result():
                    yield fut.result()
                self._async_dict[name] = self._executor.submit(self._func_dict[name])
            elif not fut:
                self._async_dict[name] = self._executor.submit(self._func_dict[name])
                

    def stop(self):
        logging.info('Stopped Network Receiver, awaiting async completion.')
        for exc_fut in self._async_dict.values():
            if exc_fut:
                if exc_fut.running():
                    exc_fut.cancel()
                while not exc_fut.done():
                    time.sleep(.01)
        logging.info('Successfully joined all threads, exiting Network Receiver.')