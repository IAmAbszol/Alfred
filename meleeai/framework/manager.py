import absl.flags
import datetime
import logging
import os
import sys

from multiprocessing import Queue

from meleeai.framework.emulator.offline import OfflineExecutor
from meleeai.framework.training.train import Train
from slippi.event import End, Start, Frame

class Manager:
    """Manager"""
    def __init__(self):
        """Manager class to handle the preparation of training/live data
        """
        # Global fields
        self._flags = absl.flags.FLAGS

        # Training framework
        self._trainer               = Train()

        # Emulator object, states, and slippi data
        self._emulator              = None
        self._emulator_state_queue  = Queue()
        self._emulator_tick        = None

        # Organized the data coming in
        self._bucket                = []
        self._published_bucket      = {}
        self._window_size           = self._flags.prediction_tick_rate
        self._window_start          = None

        # Organized predictions
        self._predictions_queue     = Queue()
        self._kalman_filter         = None

        if self._is_running_offline():
            self._emulator = OfflineExecutor()

    def __del__(self):
        while not self._emulator_state_queue.empty():
            self._emulator_state_queue.get(timeout=.001)
        self._emulator_state_queue.close()
        self._emulator_state_queue.join_thread()

        while not self._predictions_queue.empty():
            self._predictions_queue.get(timeout=.001)
        self._predictions_queue.close()
        self._predictions_queue.join_thread()

    def _is_running_offline(self):
        """Check to see if the flags specified indicate offline management.
        :return: bool
        """
        ret = False
        if not self._flags.live_emulation and self._flags.train:
            if os.path.exists(self._flags.emulator) and os.path.exists(self._flags.slippi_data):
                ret = True
        return ret

    def _release_to_train(self):
        """Retrieves the most recent batch, as a precaution, grab all incase of multiple releases.
        """
        while self._published_bucket:
            # If time-complexity becomes an issue, sack space with linked_list [time] values and time-map
            yield self._published_bucket.pop(min(self._published_bucket.keys())) 

    def check_emulator_state(self):
        """Initializes and monitors the emulator if the criteria is met for offline running.
        """
        # Currently the last state in sought after, might change later
        last_state = None
        while not self._emulator_state_queue.empty():
            state = self._emulator_state_queue.get()
            if isinstance(state, (Start, Frame.Event.Type.POST, End)):
                last_state = state

        # Very unlikely last state had more than start/end overwritten as processing is 1/60th of a second.
        if isinstance(last_state, (Start, Frame.Event.Type.POST)) and self._is_running_offline():
            self._emulator_tick = datetime.datetime.utcnow()

        # Add conditional for if time exceeds wait time for data
        if (isinstance(last_state, End) or not self._emulator.is_alive() or \
            (datetime.datetime.utcnow() - self._emulator_tick).total_seconds() >= self._flags['burnouttime']) and self._is_running_offline():
            if self._emulator.is_alive():
                self._emulator.close()
            self._emulator_tick = None
            self._emulator.execute()

    def close(self):
        """Closes the emulator process.
        """
        while not self._emulator_state_queue.empty():
            self._emulator_state_queue.get(timeout=.001)
        self._emulator_state_queue.close()
        self._emulator_state_queue.join_thread()

    def update(self, message_type, data, timestamp):
        """Updates the Manager with the latest data, deploying data if need be
        :param message_type: Type of message associated with this update
        :param data: Payload data, differentiates slightly between message_types
        :param timestamp: Timestamp associated with the update
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

        # POST only comes from players
        if isinstance(data[2], (Start, Frame.Event.Type.POST, End)):
            self._emulator_state_queue.put_nowait(data[2])
            

    def retrieve_prediction(self):
        pass