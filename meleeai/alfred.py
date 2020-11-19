import absl.app
import argparse
import datetime
import logging
import os

from functools import partial

from meleeai.framework.engine import Engine
from meleeai.utils.flags import create_flags

FORMAT = '(%(asctime)s) [%(filename)s:%(lineno)s - %(funcName)20s() ] [%(levelname)s] %(message)s'

def setup(args):
    """Begins Alfred's processing Engine.
    """
    if not os.path.exists('runtime'):
        os.makedirs('runtime')

    # Setup logging
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


