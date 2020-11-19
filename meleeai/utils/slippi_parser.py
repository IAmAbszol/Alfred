import absl.flags
import datetime
import io
import logging
import os
import pickle

from slippi.event import Frame, Start, End
from slippi.parse import _parse_event as parse_event
from slippi.parse import _parse_event_payloads as parse_event_payloads
from slippi.util import expect_bytes, unpack

class SlippiParser:
    """SlippiParser"""
    def __init__(self):
        """Initializes the parsing module for Slippi data"""
        # Global fields
        self._flags = absl.flags.FLAGS

        self.DEFAULT_PAYLOAD_SIZES = {
            54: self._flags.slippi_start_byte,
            55: self._flags.slippi_pre_byte,
            56: self._flags.slippi_post_byte,
            57: self._flags.slippi_end_byte
        }

        self._SKIP = 12


    def parse_bin(self, stream, network=True):
        """Parses the Slippi data using hohav's Slippi parser into events
        :param stream: Input stream off the socket or file
        :param network: Slippi data was retrieved off the network or via file stream
        :return: Slippi Events
        """
        events      = []
        cont        = True
        timestamp   = None

        # some streams being passed in might not have been opened yet
        if isinstance(stream, str) and os.path.isfile(stream):
            stream = io.BytesIO(open(stream, 'rb').read())
        elif not network:
            cont = False

        if network:
            seconds, microseconds = unpack('II', stream)
            timestamp             = float(f'{seconds}.{microseconds}')
        else:
            timestamp             = (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(0)).total_seconds()

        if cont:
            end_idx = stream.getbuffer().nbytes

            # Preload the payload_sizes to avoid potentially updated slippi data coming in.
            try:
                expect_bytes(b'{U\x03raw[$U#l', stream)
                (_,) = unpack('l', stream.read(4))
                self.DEFAULT_PAYLOAD_SIZES = parse_event_payloads(stream)
                logging.info('Slippi payload data has been received, modifying existing table.')
            except Exception:
                stream.seek(self._SKIP)
                pass

            # Parse the event and matches it accordingly
            while stream.tell() < end_idx and cont:
                if cont:
                    try:
                        extracted_event = parse_event(stream, self.DEFAULT_PAYLOAD_SIZES)
                    except Exception:
                        cont = False

                    if cont:
                        if isinstance(extracted_event, Start):
                            events.append((timestamp, extracted_event))
                        elif isinstance(extracted_event, Frame.Event):
                            current_frame = Frame(extracted_event.id.frame)
                            port = current_frame.ports[extracted_event.id.port]
                            if not port:
                                port = Frame.Port()
                                current_frame.ports[extracted_event.id.port] = port
                            data = port.leader
                            if extracted_event.type is Frame.Event.Type.PRE:
                                events.append((timestamp, (
                                                            extracted_event.id.frame,
                                                            extracted_event.id.port,
                                                            data.Pre(extracted_event.data)
                                            )))
                            if extracted_event.type is Frame.Event.Type.POST:
                                events.append((timestamp, (
                                                            extracted_event.id.frame,
                                                            extracted_event.id.port,
                                                            data.Post(extracted_event.data)
                                            )))
                        elif isinstance(extracted_event, End):
                            events.append((timestamp, extracted_event))
                        else:
                            logging.warning('Malformed Slippi data detected.')
                            cont = False
        return events
