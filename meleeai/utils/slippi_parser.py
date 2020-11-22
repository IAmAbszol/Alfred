import datetime
import io
import logging
import os
import pickle

from slippi.event import Frame, Start, End
from slippi.parse import ParseEvent
from slippi.parse import _parse_events as parse_events
from slippi.util import expect_bytes, unpack

class SlippiParser:
    """SlippiParser"""
    def __init__(self):
        """Initializes the parsing module for Slippi data"""
        # Global fields
        self.DEFAULT_PAYLOAD_SIZES = {54: 420, 55: 63, 56: 72, 57: 2, 58: 8, 59: 42, 60: 8, 61: 31440, 16: 516}

    def parse_bin(self, stream, network=True):
        """Parses the Slippi data using hohav's Slippi parser into events
        :param stream: Input stream off the socket or file
        :param network: Slippi data was retrieved off the network or via file stream
        :return: Slippi Events
        """
        events      = []
        cont        = True
        timestamp   = None

        def add_data_ident(x):
            events.append((timestamp, x))

        # TODO: Add support for followers
        def add_event(x):
            if isinstance(x, Frame):
                port = [idx for idx, v in enumerate(x.ports) if v is not None][0]
                data = x.ports[port].leader.pre if x.ports[port].leader.pre is not None else x.ports[port].leader.post
                events.append((timestamp, (
                                            x.index,
                                            port,
                                            data
                                        )))

        handlers = {
            ParseEvent.START: lambda x: add_data_ident(x),
            ParseEvent.FRAME: lambda x: add_event(x),
            ParseEvent.END:  lambda x: add_data_ident(x),
            ParseEvent.METADATA: lambda x: add_data_ident(x),
            ParseEvent.METADATA_RAW: lambda x: add_data_ident(x)}

        # some streams being passed in might not have been opened yet
        if isinstance(stream, str) and os.path.isfile(stream):
            stream = io.BytesIO(open(stream, 'rb').read())

        if network:
            seconds, microseconds = unpack('II', stream)
            timestamp             = float(f'{seconds}.{microseconds}')
        else:
            timestamp             = (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(0)).total_seconds()

        # Preload the payload_sizes to avoid potentially updated slippi data coming in.
        try:
            expect_bytes(b'{U\x03raw[$U#l', stream)
            (_,) = unpack('l', stream)
            _, self.DEFAULT_PAYLOAD_SIZES = parse_event_payloads(stream)
            logging.info('Slippi payload data has been received, modifying existing table.')
        except Exception as e:
            stream.seek(len(b'{U\x03raw[$U#l'))

        parse_events(stream, self.DEFAULT_PAYLOAD_SIZES, 0, handlers)
        return events

if __name__ == '__main__':

    slp = SlippiParser()
    with open('../../slippi.bin', 'rb') as fd:
        stream = io.BytesIO(fd.read())
        stream.seek(12)
        slp.parse_bin(stream, network=True)

