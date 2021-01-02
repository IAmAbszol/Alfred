#import absl.flags
import logging
import socket

class NetworkSender:

    def __init__(self):
        # Global fields
        #self._flags             = absl.flags.FLAGS
        self._ip_address        = '127.0.0.1' #self._flags.sending_ip
        self._port              = 55082 #self._flags.playerport + self._flags.alfred_port

        self._sending_socket    = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sending_socket.settimeout(1)

    def __del__(self):
        self._sending_socket.close()

    def send(self, state):
        """Sends a controller state to the Dolphin client per the configured
        address in flags.py.
        :param state: Class populated Controller instance.
        """
        assert isinstance(state, bytes), logging.error('State must be of type bytes.')
        try:
            self._sending_socket.sendto(state, (self._ip_address, self._port))
        except socket.timeout:
            logging.warning('Failed to send data to remote host.')