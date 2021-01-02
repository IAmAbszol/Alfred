import datetime
import gym.spaces as spaces
import io
import logging
import numpy as np
import os
import pickle

from slippi.event import Frame, Start, End
from slippi.parse import ParseEvent
from slippi.parse import _parse_events as parse_events
from slippi.parse import _parse_event_payloads as parse_event_payloads
from slippi.util import expect_bytes, unpack

class SlippiParser:
    """SlippiParser"""
    def __init__(self, MAX_SIZE=10):
        """Initializes the parsing module for Slippi data"""
        # Global fields
        self.DEFAULT_PAYLOAD_SIZES = {54: 420, 55: 63, 56: 72, 57: 2, 58: 8, 59: 42, 60: 8, 61: 31440, 16: 516}
        self.MAP_SIZE = MAX_SIZE

        self._slippi_data = {}

    def get_domain_restriction(self):
        """Returns a spaces.Box object with multiple lows and highs for slippi data.
        The restricted domain is with respect to Frame Pre/Post updates.
        :return: spaces.Box for both Pre and Post.
        """
        pre_frame_space = spaces.Box(
            low=np.array([0, 0, -1, -1, 0, -1, -1, -1, -1000, -1000, 0, 0, 0, 0, 0]),
            high=np.array([2**32, 2**13, 1, 1, 1000, 1, 1, 1, 1000, 1000, 1, 382, 1, 1, 1]),
            dtype=np.float64
        )
        post_frame_space = spaces.Box(
            low=np.array([0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, -1000, -1000, 0, 0, 0, 0]),
            high=np.array([1, 32, 1000, 1000, 1, 2**39, 1, 1000, 6, 2, 62, 3, 1000, 1000, 60, 382, np.finfo(np.float64).max, 99]),
            dtype=np.float64
        )
        return pre_frame_space, post_frame_space

    def parse_bin(self, stream, network=True):
        """Parses the Slippi data using hohav's Slippi parser into events
        :param stream: Input stream off the socket or file
        :param network: Slippi data was retrieved off the network or via file stream
        :return: Slippi Events
        """
        events      = []
        timestamp   = None

        def add_data_ident(x):
            events.append((timestamp, x))

        # TODO: Add support for followers
        def add_event(x):
            if isinstance(x, Frame):
                port = [idx for idx, v in enumerate(x.ports) if v is not None][0]
                if (x.index, port) in self._slippi_data:
                    data = x.ports[port].leader.post
                    if data:
                        events.append((timestamp, (
                            x.index,
                            port,
                            (self._slippi_data[(x.index, port)], data)
                        )))
                else:
                    data = x.ports[port].leader.pre
                    if data:
                        self._slippi_data[(x.index, port)] = data

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
        except Exception:
            stream.seek(len(b'{U\x03raw[$U#l'))

        # TODO: Calculate total_size
        parse_events(stream, self.DEFAULT_PAYLOAD_SIZES, 0, handlers)

        # Take dictionary, if threshold is met, delete oldest key
        if len(list(self._slippi_data.keys())) > self.MAP_SIZE:
            self._slippi_data.pop(min(list(self._slippi_data.keys())))
        return events

    def translate_to_array(self, data):
        """Translates Pre/Post slippi data to a 1-D array.
        :param data: Slippi data
        :return: NumPy 1-D Array.
        """
        assert isinstance(data, Frame), logging.error('Data must be of type Frame.')

        def translate_pre(pre):
            return np.array([
                pre.buttons.logical,
                pre.buttons.physical,
                pre.cstick.x,
                pre.cstick.y,
                pre.damage,
                pre.direction,
                pre.joystick.x,
                pre.joystick.y,
                pre.position.x,
                pre.position.y,
                pre.raw_analog_x,
                pre.state,
                pre.triggers.logical,
                pre.triggers.phyiscal.l,
                pre.triggers.physical.r
            ])

        def translate_post(post):
            return np.array([
                post.airborne,
                post.character,
                post.combo_count,
                post.damage,
                post.direction,
                post.flags,
                post.ground,
                post.hit_stun,
                post.jumps,
                post.l_cancel, 
                post.last_attack_landed,
                post.last_hit_by,
                post.position.x,
                post.position.y,
                post.shield,
                post.state,
                post.state_age, 
                post.stocks
            ])

        translated = None
        try: translated = translate_pre(data) 
        except Exception: pass
        try: translated = translate_post(data)
        except Exception: pass
        return translated