import absl.flags
import datetime
import json
import logging
import os
import pickle
import subprocess
import threading

from multiprocessing import Process, Queue

import slippi

from meleeai.utils.util import should_play
from slippi.game import Game

class AsynchronousFileReader(threading.Thread):
    """Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    """

    def __init__(self, fd, queue):
        #assert isinstance(queue, Queue)
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue
        self._close = False

    def run(self):
        """The body of the tread: read lines and put them on the queue."""
        for line in iter(self._fd.readline, ''):
            if line.decode('utf-8') == '' or self._close:
                break
            self._queue.put(line)

    def eof(self):
        """Check whether there is no more content to expect."""

    def close(self):
        """Closes the string reader."""
        self._close = True

class OfflineExecutor:

    def __init__(self):
        # Global fields
        self._flags             = absl.flags.FLAGS
        self._frame_length      = self._flags.min_frame_length
        self._no_lras            = self._flags.no_lras

        self._emulator          = None
        self._slippi_com_file   = 'slippi_com.json'
        self._slippi_files = Queue()

        self._stdout_queue      = None
        self._stdout_reader     = None

        # TODO: Add load on files and take into account system RAM.
        total_read = 0
        logging.info('Processing Slippi file directory provided for any .slp files, please wait.')
        for f in os.listdir(self._flags.slippi_data):
            if f.endswith('.pslp'):
                with open(os.path.join(self._flags.slippi_data, f), 'rb') as fd:
                    unpickled_data = pickle.load(fd)
                    if unpickled_data:
                        for (slippi_port, opponent_port), slippi_file in unpickled_data:
                            if os.path.exists(os.path.join(self._flags.slippi_data, slippi_file)):
                                self._slippi_files.put(((slippi_port, opponent_port), os.path.join(self._flags.slippi_data, slippi_file)))
                            total_read += 1
        logging.info(f'Successfully loaded {self._slippi_files.qsize()}/{total_read} ({round(self._slippi_files.qsize()/total_read * 100, 2)}%).')


    def __del__(self):
        while self._slippi_files.qsize():
            self._slippi_files.get(timeout=.001)
        self._slippi_files.close()
        self._slippi_files.join_thread()

        self.close()

    def _check_state(self):
        """Checks to see if the integrity of paths being used.
        return: Boolean
        """
        return os.path.exists(self._flags.emulator) and os.path.exists(self._flags.melee_iso)

    def _consume(self, command):
        """
        Communicates to process and reads any data provided by the Queue.
        :param command: Commnad to execute, assumes modified Dolphin copy is being used.
        """
        self._emulator = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self._stdout_queue = Queue()
        self._stdout_reader = AsynchronousFileReader(self._emulator.stdout, self._stdout_queue)
        self._stdout_reader.start()

    def _prepare_script(self, slippi_file):
        """
        Creates and writes a communication file for the Dolphin Slippi to communicate with.
        :param slippi_file: Absolute path to .slp file for replay.
        """
        if not os.path.exists(slippi_file):
            raise IOError('Slippi replay file does not exist!')
        json_script = {
                "mode":"normal",
                "replay":slippi_file,
                "isRealTimeMode":False,
                "commandId":"adccbe9a0e1ed0a1a9195a35"
            }
        fp = open(self._slippi_com_file, 'w')
        fp.write(json.dumps(json_script))
        fp.flush()
        fp.close()

    def close(self):
        """Closes the subprocess and prints any messages that might've been received
        during runtime. Process will only ever terminate on close().
        """
        if self.is_alive():
            self._emulator.terminate()

            #while not self._stdout_reader.eof():
            #    logging.info(self._stdout_queue.get())

            self._stdout_reader.close()
            self._stdout_reader.join()

            self._emulator.stdout.close()
            self._emulator = None

    def execute(self):
        """Starts the emulator if all the criterion has passed.
        """
        if not self.is_alive():
            if self._slippi_files.qsize():
                ports, slippi_file = self._slippi_files.get()
                logging.warning(f'Replaying. Observing Port {ports[0]} : {slippi_file}')
                self._prepare_script(slippi_file)
                self._consume([self._flags.emulator, '-i', self._slippi_com_file, '-e', self._flags.melee_iso])

    def is_alive(self):
        """Checks to see if the emulator process is still alive.
        :return: Boolean
        """
        #print(self._check_state(), not self._emulator is None, 'None' if self._emulator is None else self._emulator.poll() is None, '=', True if self._check_state() and (self._emulator is not None and self._emulator.poll() is None) else False)
        return True if self._check_state() and (not self._emulator is None and self._emulator.poll() is None) else False
