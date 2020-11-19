from slippi.event import ParseEvent
from slippi.parse import parse
from slippi.util import *


class Game(Base):
    """Replay data from a game of Super Smash Brothers Melee."""

    def __init__(self, input):
        """Parses Slippi replay data from `input` (stream or path)."""

        self.start = None
        """:py:class:`slippi.event.Start`: Information about the start of the game"""

        self.frames = []
        """list(:py:class:`slippi.event.Frame`): Every frame of the game, indexed by frame number"""

        self.end = None
        """:py:class:`slippi.event.End`: Information about the end of the game"""

        self.metadata = None
        """:py:class:`slippi.metadata.Metadata`: Miscellaneous data not directly provided by Melee"""

        self.metadata_raw = None
        """dict: Raw JSON metadata, for debugging and forward-compatibility"""

        handlers = {
            ParseEvent.START: lambda x: setattr(self, 'start', x),
            ParseEvent.FRAME: lambda x: self.frames.append(x),
            ParseEvent.END: lambda x: setattr(self, 'end', x),
            ParseEvent.METADATA: lambda x: setattr(self, 'metadata', x),
            ParseEvent.METADATA_RAW: lambda x: setattr(self, 'metadata_raw', x)}

        parse(input, handlers)

    def _attr_repr(self, attr):
        if attr == 'frames':
            return 'frames=[...](%d)' % len(self.frames)
        elif attr != 'metadata_raw':
            return super()._attr_repr(attr)
        else:
            return None
