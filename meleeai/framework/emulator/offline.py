import absl.flags
import datetime
import json
import logging
import os
import subprocess
import threading

from multiprocessing import Process, Queue

import slippi

from slippi.game import Game

class AsynchronousFileReader(threading.Thread):
    """Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    """

    def __init__(self, fd, queue):
        assert isinstance(queue, Queue)
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
            if f.endswith('.slp'):
                total_read += 1
                ports = self._should_play(os.path.join(self._flags.slippi_data, f))
                if not -1 in ports:
                    self._slippi_files.put((ports, os.path.join(self._flags.slippi_data, f)))
                    logging.info(f'Added {f} to queue.')
        logging.info(f'Successfully loaded {self._slippi_files.qsize()}/{total_read} ({round(self._slippi_files.qsize()/total_read * 100, 2)}%).')

    def __del__(self):
        while not self._slippi_files.empty():
            self._slippi_files.get(timeout=.001)
        self._slippi_files.close()
        self._slippi_files.join_thread()

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

    def _should_play(self, slippi_file):
        """Determines whether the criterion to run has been met.
        :param slippi_file: Absolute path to .slp file for replay.
        :return: Tuple [-1 == Not a match, first index is observable player.]
        """
        slippi_port = -1
        opponent_port = -1

        try:
            slippi_game = Game(slippi_file)

            slippi_version = tuple(list(map(int, str(slippi_game.start.slippi.version).split('.'))))
            if slippi_version >= tuple(list(map(int, self._flags.min_slippi_version.split('.')))):
                if slippi_version >= (2,0,0):
                    if len(slippi_game.frames) >= self._flags.min_frame_length:
                        if self._flags.no_lras:
                            if slippi_game.end and not slippi_game.end.lras_initiator:
                                return (slippi_port, opponent_port)
                        start_frame = slippi_game.start.__dict__
                        if not start_frame['is_teams'] and start_frame['stage'] == self._flags.stage_id:
                            ports = [False, False]
                            for player_index, player in enumerate(start_frame['players']):
                                if player is None:
                                    continue
                                player_dict = player.__dict__
                                if player_dict['character'] == self._flags.player_character_id and \
                                        player_dict['costume'] == self._flags.player_costume_id:
                                    ports[0] = player_index
                                elif player_dict['character'] == self._flags.opponent_character_id:
                                    ports[1] = player_index
                            if not any(ports):
                                slippi_port, opponent_port = -1, -1
                            else:
                                slippi_port, opponent_port = ports
        except slippi.parse.ParseError as pe:
            logging.error(f'Received parsing error: {pe}.')

        return  (slippi_port, opponent_port)

    def close(self):
        """Closes the subprocess and prints any messages that might've been received
        during runtime. Process will only ever terminate on close().
        """
        if self.is_alive():
            self._emulator.terminate()

            while not self._stdout_reader.eof():
                logging.info(self._stdout_queue.get())

            self._stdout_reader.close()
            self._stdout_reader.join()

            self._emulator.stdout.close()
            self._emulator = None

    def execute(self):
        """Starts the emulator if all the criterion has passed.
        """
        if self.is_alive():
            logging.warning('Emulator process is still open, please wait and try again later.')
        else:
            while not self._slippi_files.empty():
                ports, slippi_file = self._slippi_files.get()
                logging.warning(f'Replaying. Observing Port {ports[0]} : {slippi_file}')

                self._prepare_script(slippi_file)

                break

    def is_alive(self):
        """Checks to see if the emulator process is still alive.
        :return: Boolean
        """
        return True if self._emulator is not None and self._emulator.poll() is None else False
