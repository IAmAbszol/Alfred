import heapq
import logging
import socket
import time
import threading

from meleeai.utils.video_parser import VideoParser
from meleeai.utils.thread_runner import ThreadRunner

class NetworkReceiver(ThreadRunner):

    def __init__(self, network_in, configured_ports):

        self._network_in = network_in

        # Setup video port
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_socket.bind(('localhost', configured_ports['video']))
        self.video_socket.settimeout(1)

        self._controller_thread = None
        self._slippi_thread     = None
        self._video_thread      = None
        self._run               = True

    def _listen_video(self):
        video_parser = VideoParser()
        while self._run:
            try:
                data_str, _ = self.video_socket.recvfrom((2**16) - 1)
                if video_parser.update(data_str):
                    if not self._network_in.closed and self._network_in.writable and not self._network_in.poll():
                        self._network_in.send(video_parser.get_completed_images()[0])
            except socket.timeout:
                logging.warning('Failed to receive any data from video socket.')    
            
            time.sleep(.001)

    def run(self):
        self._run = True
        self._video_thread = threading.Thread(target=self._listen_video)
        
        self._video_thread.start()
        logging.info('Started Network Communication Receiver thread.')        

    def stop(self):
        self._network_in.close()

        self._run = False
        logging.info('Stopped Network Communication Receiver, awaiting thread completion.')

        self._video_thread.join()
        logging.info('Successfully joined all threads, exiting Network Communication Receiver.')