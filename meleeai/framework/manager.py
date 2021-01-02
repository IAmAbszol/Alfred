import absl.flags
import datetime
import logging
import os
import sys

from multiprocessing import Queue

from meleeai.framework.emulator.offline import OfflineExecutor
from slippi.event import End, Start, Frame


class Manager:
    """Data Manager Class"""
    def __init__(self):
        """Manager class to handle the preparation of training/live data
        """
        # Global fields
        self._flags = absl.flags.FLAGS

        # Emulator object, states, and slippi data
        self._emulator              = None
        self._emulator_state_queue  = Queue()
        self._emulator_tick         = None

        # Organized the data coming in
        self._bucket                = Queue()
        self._published_bucket      = []
        self._window_size           = self._flags.prediction_tick_rate
        self._window_start          = None

        # Organized predictions
        self._predictions_queue     = Queue()
        self._kalman_filter         = None

        if self._is_running_offline():
            self._emulator = OfflineExecutor()

    def __del__(self):
        while self._bucket.qsize():
            self._bucket.get()
        self._bucket.close()
        self._bucket.join_thread()

        while self._emulator_state_queue.qsize():
            self._emulator_state_queue.get()
        self._emulator_state_queue.close()
        self._emulator_state_queue.join_thread()

        while self._predictions_queue.qsize():
            self._predictions_queue.get()
        self._predictions_queue.close()
        self._predictions_queue.join_thread()

    def _is_running_offline(self):
        """Check to see if the flags specified indicate offline management.
        :return: bool
        """
        ret = False
        #print(not self._flags.live_emulation, self._flags.train, os.path.exists(self._flags.emulator), os.path.exists(self._flags.slippi_data))
        if not self._flags.live_emulation and self._flags.train:
            if os.path.exists(self._flags.emulator) and os.path.exists(self._flags.slippi_data):
                ret = True
        return ret

    def check_emulator_state(self):
        """Initializes and monitors the emulator if the criteria is met for offline running.
        """
        # Currently the last state in sought after, might change later
        last_state = None
        while not self._emulator_state_queue.empty():
            state = self._emulator_state_queue.get()
            if isinstance(state, (Start, Frame, End)):
                last_state = state

        # Very unlikely last state had more than start/end overwritten as processing is 1/60th of a second.
        if self._is_running_offline() and isinstance(last_state, (Start, Frame)):
            self._emulator_tick = datetime.datetime.utcnow()

        # Add conditional for if time exceeds wait time for data
        if self._is_running_offline() and (isinstance(last_state, End) or \
            (self._emulator_tick and (datetime.datetime.utcnow() - self._emulator_tick).total_seconds() >= self._flags.burnouttime)):
            if self._emulator.is_alive():
                self._emulator.close()
            self._emulator_tick = None

        #print(self._is_running_offline(), self._emulator_tick, not self._emulator.is_alive())
        if self._is_running_offline() and self._emulator_tick is None and not self._emulator.is_alive():
            self._emulator.execute()

    def close(self):
        """Closes the emulator process.
        """
        while not self._emulator_state_queue.empty():
            self._emulator_state_queue.get(timeout=.001)
        self._emulator_state_queue.close()
        self._emulator_state_queue.join_thread()

    def get_published(self):
        """Returns the current published_bucket.
        :return: List
        """
        return self._published_bucket

    def update(self, message_type, data, timestamp):
        """Updates the Manager with the latest data, deploying data if need be
        :param message_type: Type of message associated with this update
        :param data: Payload data, differentiates slightly between message_types
        :param timestamp: Timestamp associated with the update
        """
        if self._window_start is None:
            self._window_start = timestamp
        # Timestamp triggers new bucket to be created, previous is published
        if (self._window_start + datetime.timedelta(milliseconds=self._window_size)) < timestamp:
            self._window_start = timestamp - \
                datetime.timedelta(((timestamp - datetime.datetime.fromtimestamp(0)).total_seconds() % self._window_size))
            if self._bucket.qsize() > 0:
                self._published_bucket.clear()
            while self._bucket.qsize() > 0:
                self._published_bucket.append(self._bucket.get())

        # POST only comes from players
        if isinstance(data, (Start, End)):
            self._emulator_state_queue.put_nowait(data)
        else:
            if isinstance(data, Frame):
                self._emulator_state_queue.put_nowait(data[2])
            # TODO: Message type == Controller, skip?
            self._bucket.put_nowait((message_type, timestamp, data))