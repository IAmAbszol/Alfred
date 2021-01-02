import datetime
import logging

from meleeai.utils.message_type import MessageType

class Data:

    def __init__(self, message_type, timestamp, data):
        assert isinstance(message_type, MessageType), logging.error(f'message_type must be of type MessageType, not {message_type}.')
        assert isinstance(timestamp, datetime.datetime), logging.error(f'timestamp must be of type Datetime, not {timestamp}.')
        self._type          = message_type
        self._timestamp     = timestamp
        self._data          = data


    def get(self):
        return (self._type, self._timestamp, self._data)

    def __instancecheck__(self, other):
        return isinstance(self, other.__class__)

class ControllerData(Data):

    def __init__(self, message_type, timestamp, data):
        Data.__init__(self, message_type, timestamp, data)


class SlippiData(Data):

    def __init__(self, message_type, timestamp, data):
        Data.__init__(self, message_type, timestamp, data)

class VideoData(Data):

    def __init__(self, message_type, timestamp, data):
        Data.__init__(self, message_type, timestamp, data)