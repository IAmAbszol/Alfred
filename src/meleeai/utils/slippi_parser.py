import io
import logging
import os
import pickle
import struct

from meleeai.framework.configuration import ConfigurationLoader
from slippi.event import Frame, Start, End
from slippi.parse import _parse_event as parse_event
from slippi.parse import _parse_event_payloads as parse_event_payloads
from slippi.util import expect_bytes, unpack

class SlippiParser:

    def __init__(self):
        self.DEFAULT_PAYLOAD_SIZES = ConfigurationLoader().get_config()['slippi']

    def parse_bin(self, stream):
        """
        Parses the Slippi data using hohav's Slippi parser into events.
        :param stream: Input stream off the socket.
        :return: Slippi Event
        """
        event   = None
        cont    = True
        # Preload the payload_sizes to avoid potentially updated slippi data coming in.
        try:
            expect_bytes(b'{U\x03raw[$U#l', stream)
            (_,) = unpack('l', stream.read(4))
            self.DEFAULT_PAYLOAD_SIZES = parse_event_payloads(stream)
            logging.info('Slippi payload data has been received, modifying existing table.')
            cont = False
        except Exception:
            stream.seek(0)
            pass

        # Parse the event and matches it accordingly
        if cont:
            try:
                extracted_event = parse_event(stream, self.DEFAULT_PAYLOAD_SIZES)
            except Exception:
                cont = False

            if cont:
                if isinstance(extracted_event, Start):
                    event = extracted_event
                elif isinstance(extracted_event, Frame.Event):
                    current_frame = Frame(extracted_event.id.frame)
                    port = current_frame.ports[extracted_event.id.port]
                    if not port:
                        port = Frame.Port()
                        current_frame.ports[extracted_event.id.port] = port
                    data = port.leader
                    if extracted_event.type is Frame.Event.Type.PRE:
                        event = data.Pre(extracted_event.data)
                    if extracted_event.type is Frame.Event.Type.POST:
                        event = data.Post(extracted_event.data)
                elif isinstance(extracted_event, End):
                    event = extracted_event
                else:
                    logging.warning('Malformed Slippi data detected.')
        return event

    def parse_file(self, bin_file):
        if os.path.exists(bin_file):
            with open(bin_file, 'rb') as fd:
                pkld_slippi_data = pickle.load(fd)
                for slippi_data in pkld_slippi_data:
                    data_io = io.BytesIO(slippi_data[4:])

                    # Preload the payload_sizes to avoid potentially updated slippi data coming in.
                    try:
                        expect_bytes(b'{U\x03raw[$U#l', data_io)
                        (_,) = unpack('l', data_io.read(4))
                        self.DEFAULT_PAYLOAD_SIZES = parse_event_payloads(data_io)
                        continue
                    except Exception:
                        data_io.seek(0)
                        pass

                    # Parse the event and match it accordingly
                    try:
                        event = parse_event(data_io, self.DEFAULT_PAYLOAD_SIZES)
                    except Exception:
                        continue

                    if isinstance(event, Start):
                        print(event)
                    elif isinstance(event, Frame.Event):
                        # TODO: Follow current_frame and how its used to build the event data blob
                        current_frame = Frame(event.id.frame)
                        port = current_frame.ports[event.id.port]
                        if not port:
                            port = Frame.Port()
                            current_frame.ports[event.id.port] = port
                        data = port.leader
                        if event.type is Frame.Event.Type.PRE:
                            data._pre = data.Pre(event.data)
                            print(data._pre)
                        if event.type is Frame.Event.Type.POST:
                            data._post = data.Post(event.data)
                            print(data._post)
                    elif isinstance(event, End):
                        print(event)
                    else:
                        print('ERROR!')
                        continue

if __name__ == '__main__':
    slippi = SlippiParser()
    slippi.parse_file('slippi_in.pkl')
