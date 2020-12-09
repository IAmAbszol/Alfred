import absl.app
import argparse
import datetime
import logging
import os

from termcolor import colored

from meleeai.framework.engine import Engine
from meleeai.utils.flags import create_flags

COLORS = {
    'WARNING': 'yellow',
    'INFO': 'white',
    'DEBUG': 'grey',
    'CRITICAL': 'red',
    'ERROR': 'red'}


_old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    l = record.levelname
    record.levelname_colored = colored(l, COLORS.get(l, 'white'))
    return record

FORMAT = '(%(asctime)s) [%(filename)s:%(lineno)s - %(funcName)20s() ] [%(levelname_colored)s] %(message)s'

def setup(args):
    """Begins Alfred's processing Engine.
    """
    if not os.path.exists('runtime'):
        os.makedirs('runtime')

    # Setup logging
    logging.setLogRecordFactory(record_factory)
    logging.basicConfig(
        level=logging.INFO,
        format=FORMAT,
        handlers=[
            logging.FileHandler('runtime/log_{}.log'.format(datetime.datetime.strftime(datetime.datetime.utcnow(), '%Y%m%d%H%M%S%f'))),
            logging.StreamHandler()
        ]
    )

    with Engine() as engine:
        engine.main()

def main():
    """Entry point for Alfred
    """
    create_flags()
    absl.app.run(setup)

if __name__ == '__main__':
    create_flags()
    absl.app.run(setup)


