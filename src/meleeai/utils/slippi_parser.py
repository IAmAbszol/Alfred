import io
import logging
import os
import pickle

from meleeai.framework.configuration import ConfigurationLoader
from slippi.event import Frame, Start, End
from slippi.parse import _parse_event as parse_event
from slippi.parse import _parse_event_payloads as parse_event_payloads
from slippi.util import expect_bytes, unpack

class SlippiParser:

    def __init__(self):
        self.DEFAULT_PAYLOAD_SIZES = ConfigurationLoader().get_config()['slippi']

        self._SKIP = 12

    def parse_bin(self, stream):
        """
        Parses the Slippi data using hohav's Slippi parser into events.
        :param stream: Input stream off the socket.
        :return: Slippi Event
        """
        events = []
        
        cont    = True
        end_idx = stream.getbuffer().nbytes
        seconds, microseconds = unpack('II', stream)
        
        # Preload the payload_sizes to avoid potentially updated slippi data coming in.
        try:
            expect_bytes(b'{U\x03raw[$U#l', stream)
            (_,) = unpack('l', stream.read(4))
            self.DEFAULT_PAYLOAD_SIZES = parse_event_payloads(stream)
            logging.info('Slippi payload data has been received, modifying existing table.')
            cont = False
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
                        events.append(float(f'{seconds}{microseconds}'), extracted_event)
                    elif isinstance(extracted_event, Frame.Event):
                        current_frame = Frame(extracted_event.id.frame)
                        port = current_frame.ports[extracted_event.id.port]
                        if not port:
                            port = Frame.Port()
                            current_frame.ports[extracted_event.id.port] = port
                        data = port.leader
                        if extracted_event.type is Frame.Event.Type.PRE:
                            events.append((float(f'{seconds}{microseconds}'), data.Pre(extracted_event.data)))
                        if extracted_event.type is Frame.Event.Type.POST:
                            events.append((float(f'{seconds}{microseconds}'), data.Post(extracted_event.data)))
                    elif isinstance(extracted_event, End):
                        events.append((float(f'{seconds}{microseconds}'), extracted_event))
                    else:
                        logging.warning('Malformed Slippi data detected.')
                        cont = False

                    

        return events