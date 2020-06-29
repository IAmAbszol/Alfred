import datetime

from meleeai.framework.configuration import ConfigurationLoader

class Manager:

    def __init__(self):
        """
        Manager class to handle the preparation of training/live data.
        """
        self._bucket                = []
        self._published_bucket      = {}
        self._window_size           = ConfigurationLoader().get_config()['alfred']['tick_rate']
        self._window_start          = None

    def update(self, message_type, data, timestamp):
        """
        Updates the Manager with the latest data, deploying data if need be.
        :param message_type: Type of message associated with this update.
        :param data: Payload data, differentiates slightly between message_types.
        :param timestamp: Timestamp associated with the update.
        """
        if self._window_start is None:
            self._window_start = timestamp
        # Timestamp triggers new bucket to be created, previous is published
        if (self._window_start + self._window_size) < timestamp:
            self._window_start = timestamp - (timestamp % self._window_size)
            if self._bucket:
                self._published_bucket[self._window_start] = self._bucket[:]
                self._bucket.clear()
        self._bucket.append((message_type, timestamp, data))

    def retrieve(self):
        """
        Retrieves any available data from the data manager.
        :return: List of data.
        """
        if self._published_bucket:
            # TODO: Make this into a one-liner? 
            bucket_time = min(self._published_bucket.keys())
            return self._published_bucket.pop(bucket_time)
