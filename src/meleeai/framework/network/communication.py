import datetime
import logging

from io import BytesIO

from meleeai.utils.thread_runner import ThreadRunner
from meleeai.framework.network.receiver import NetworkReceiver

class NetworkCommunication(ThreadRunner):

    def __init__(self, network_in, inbound_ports : dict, outbound_port : int):
        """
        Hanldes network communication for Alfred by providing a simple API of receive() and send()
        :param network_in: Pipe for network data to be written to amongst the three threads.
        :param inbound_ports: Controller, Slippi, and Video ports
        :param outbound_port: Controller port for Alfred prediction
        """
        if not (isinstance(inbound_ports, dict) or len(inbound_ports.keys()) != 3):
            logging.error('Inbound_ports must be of type list and of length 3.')
            exit(1)

        if not isinstance(outbound_port, int):
            logging.error('Outbound_port must be of type int.')
            exit(1)

        # Protected attributes of NetworkCommunication
        self._inbound_ports = inbound_ports
        self._output_ports = outbound_port

        # Objects known to NetworkCommunication
        self.network_receiver = NetworkReceiver(network_in, self._inbound_ports)

    def run(self):
        self.network_receiver.run()
        logging.info('Starting Network Communication thread runners.')        

    def stop(self):
        self.network_receiver.stop()