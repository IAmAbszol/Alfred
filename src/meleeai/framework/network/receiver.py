import heapq
import logging
import socket
import time
import threading

from io import BytesIO

from meleeai.utils.message_type import MessageType
from meleeai.utils.thread_runner import ThreadRunner
from meleeai.utils.video_parser import VideoParser
from meleeai.utils.slippi_parser import SlippiParser

class NetworkReceiver(ThreadRunner):

    def __init__(self, network_in, configured_ports):
        """
        Network receiver class for explicity set ports defined in codebase.
        :param network_in: Pipeline to main engine that expects a tuple'd (Messagetype.ENUM, payload)
        :param configured_ports: Dictionary from loaded config
        """
        self._network_in = network_in

        # Setup slippi port
        self._slippi_socket     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._slippi_socket.bind(('localhost', configured_ports['slippi']))
        self._slippi_socket.settimeout(1)

        # Setup video port
        self._video_socket      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._video_socket.bind(('localhost', configured_ports['video']))
        self._video_socket.settimeout(1)

        self._thread_pool       = []
        self._run               = True

    def _is_network_ready(self):
        return not self._network_in.closed and self._network_in.writable and not self._network_in.poll()

    # TODO: Might be keen to separate video, slippi, and controller pipes.
    #       The throughput might be bottlenecked and loss of data is surely to happen.
    def _listen_slippi(self):
        slippi_parser = SlippiParser()
        while self._run:
            try:
                data_str, _ = self._slippi_socket.recvfrom(512)
                event       = slippi_parser.parse_bin(BytesIO(data_str[4:]))
                if event:
                    if self._is_network_ready():
                        self._network_in.send((MessageType.SLIPPI, (_, event)))
            except socket.timeout:
                logging.warning('Failed to receive any data from slippi socket.')        
            except OSError:
                logging.warning('Slippi receiver pipeline has been closed')
            time.sleep(.001)    

    def _listen_video(self):
        video_parser = VideoParser()
        while self._run:
            try:
                data_str, _ = self._video_socket.recvfrom((2**16) - 1)
                if video_parser.update(data_str):
                    if self._is_network_ready():
                        video_captures = video_parser.get_completed_images()
                        if video_captures:
                            self._network_in.send((MessageType.VIDEO, video_captures[0]))
            except socket.timeout:
                logging.warning('Failed to receive any data from video socket.')    
            except OSError:
                logging.warning('Video receiver pipeline has been closed')
            time.sleep(.001)

    def run(self):
        self._run = True
        
        # Add threads to pool
        self._thread_pool.append(threading.Thread(target=self._listen_slippi))
        self._thread_pool.append(threading.Thread(target=self._listen_video))
        
        for thread in self._thread_pool:
            thread.start()

        logging.info('Started Network Communication Receiver thread.')        

    def stop(self):
        self._network_in.close()

        self._run = False
        logging.info('Stopped Network Communication Receiver, awaiting thread completion.')

        for active_thread in self._thread_pool:
            if active_thread.isAlive():
                active_thread.join()
        logging.info('Successfully joined all threads, exiting Network Communication Receiver.')