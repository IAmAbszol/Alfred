import absl.app
import absl.flags
import datetime
import os
import logging
import math
import multiprocessing
import pickle
import threading

import slippi

from meleeai.utils.flags import create_flags
from meleeai.utils.util import should_play
from slippi.game import Game

# Setup logging
FORMAT = '(%(asctime)s) [%(filename)s:%(lineno)s - %(funcName)20s() ] [%(levelname)s] %(message)s'

logging.basicConfig(
   level=logging.DEBUG,
   format=FORMAT,
   handlers=[
      logging.StreamHandler()
   ]
)

def write(data, starting_index, ending_index, name='processed_%s_%s_%s.pslp'):
   """Writes .pslp data to disk.
   :param data: Data to write to disk.
   :param starting_index: Starting index that data collected on.
   :param ending_index: Ending index that data collected on.
   :param name: Processed data, must contain two formatters.
   """
   with open(name % (len(data), starting_index, ending_index), 'wb') as fd:
      pickle.dump(data, fd)

def processor(name, grouped_files, flags):
   verified_files = []
   for (_, slippi_file) in grouped_files:
      slippi_port, opponent_port = should_play(slippi_file)
      if not -1 in [slippi_port, opponent_port]:
         verified_files.append(((slippi_port, opponent_port), os.path.split(slippi_file)[1]))
   write(verified_files, grouped_files[0][0], grouped_files[-1][0])


def main(args):

   flags = absl.flags.FLAGS

   processes = []
   local_cpu_count = multiprocessing.cpu_count()

   slippi_data = flags.slippi_data

   slippi_files = [(idx, os.path.join(slippi_data, f)) for idx, f in enumerate(os.listdir(slippi_data)) if f.endswith('.slp')]

   grouped_slippi_files = []
   developing_group = []

   partition_size = math.floor(len(slippi_files)/local_cpu_count)

   for idx, x in enumerate(slippi_files):
      developing_group.append(x)
      if (idx % partition_size == 0 and idx != 0):
         grouped_slippi_files.append(developing_group)
         developing_group = []
   if developing_group:
      if grouped_slippi_files:
         grouped_slippi_files[-1].extend(developing_group)
      else:
         grouped_slippi_files.append(developing_group)

   for group_idx, group in enumerate(grouped_slippi_files):
      processes.append(multiprocessing.Process(target=processor, args=('process_%s_' % group_idx, group, flags)))
      processes[-1].start()

   for process in processes:
      process.join()

if __name__ == '__main__':
   create_flags()
   absl.app.run(main)

