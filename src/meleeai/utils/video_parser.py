import array
import logging
import struct
import sys

from io import BytesIO

from meleeai.utils.message_type import MessageType

class VideoParser:

    def __init__(self, MAX_SIZE=10):
        self.HEADER             = '>I B B 2i 4I'
        self.HEADER_SIZE        = struct.calcsize(self.HEADER)
        self.HEADER_UNPACK      = struct.Struct(self.HEADER).unpack
        self.MAP_SIZE           = MAX_SIZE

        self._video_data = {}

    def _concat_image(self, frame_segments):
        raw = None
        total_bs = 0
        for data in frame_segments:
            if not raw:
                raw = data['raw']
            else:
                raw += data['raw']
            total_bs += data['block_size']
        return array.array('B', raw), total_bs

    # TODO: Remove abs() if its desired that left-hand side is more favorable than right-hand side.
    def _get_completed_image(self, timestamp=0):
        """
        Gets the image closest to the provided timestamp.
        :param timestamp: Timestamp of frames. Keep relative to data rather than system as Windows Dolphin
                          time is currently bugged.
        :return: frame, timestamp, min_tim
        """
        closest_frame, closest_time, time_difference = None, None, sys.maxsize
        for frame, list_data in self._video_data.items():
            for data in list_data:
                if (data['index'] + 1) == data['total_segments']:
                    if not closest_frame or abs(timestamp - data['timestamp']) < time_difference:
                        closest_frame, closest_time, time_difference = frame, data['timestamp'], abs(timestamp - data['timestamp'])
        return closest_frame, closest_time, time_difference

    def clear(self):
        self._video_data.clear()

    def get_completed_images(self):
        """
        Gets all the
        """
        completed_images = []
        while self._video_data:
            frame, timestamp, _ = self._get_completed_image()
            if frame:
                completed_images.append((timestamp, self._concat_image(self._video_data[frame])[0]))
                self._video_data.pop(frame)
            else:
                break
        return completed_images

    def update(self, data_str):
        # Parse the message
        ret = True
        if len(data_str) < self.HEADER_SIZE:
            logging.error('Data string provided is too small for header to parse.')
            ret = False
        (frame, segment, total_segments, width, height, block_size, _, seconds, microseconds)= self.HEADER_UNPACK(data_str[:30])
        if block_size > len(data_str[30:]):
            logging.error('Data string provided is too small for image to be parsed.')
            ret = False

        # Take parsed message and place into dict
        if frame not in self._video_data:
            self._video_data[frame] = []
        self._video_data[frame].append({
            'index' : segment,
            'total_segments' : total_segments,
            'block_size' : block_size,
            'width' : width,
            'height' : height,
            'timestamp' : int(f'{seconds}{microseconds}'),
            'raw' : list(struct.unpack('>' + 'B' * block_size, data_str[30:])) # big endian? 
        })

        # Take dictionary, if threshold is met, delete oldest key
        if len(list(self._video_data.keys())) > self.MAP_SIZE:
            self._video_data.pop(min(list(self._video_data.keys())))

        return ret