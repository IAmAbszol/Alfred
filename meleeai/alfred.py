import absl.app
import absl.flags
import argparse
import datetime
import logging
import os
import struct

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
        force=True,
        level=logging.INFO,
        format=FORMAT,
        handlers=[
            logging.FileHandler('runtime/log_{}.log'.format(datetime.datetime.strftime(datetime.datetime.utcnow(), '%Y%m%d%H%M%S%f'))),
            logging.StreamHandler()
        ]
    )

    # Verify flags set in place
    verify()

    with Engine() as engine:
        engine.main()

def verify():
    """Verifies the integrity of the flags set, certain conditions unchecked might lead
    to Dolphin being explosively opened. Add onto these checks for any additional constraints
    added to the system.
    """
    flags = absl.flags.FLAGS

    # Ensure the Melee ISO exists and is infact an iso
    if not flags.live_emulation:
        assert os.path.exists(flags.melee_iso), 'Missing Melee ISO for offline replay.'
        with open(flags.melee_iso, 'rb') as fd:
            fd.seek(0, 2)
            length = fd.tell()
            fd.seek(0, 0)
            fmt = '<' + 'B'*54
            assert length > struct.calcsize(fmt), f'File must be of at least length {struct.calcsize(fmt)}, found size to be {length}.'
            header = ''.join([chr(x) for x in struct.unpack(fmt, fd.read(54))])
            assert header == 'GALE01\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Â3\x9f=Super Smash Bros Melee', \
                'Melee ISO Header must match GALE01 ...'

def main():
    """Entry point for Alfred
    """
    create_flags()
    absl.app.run(setup)

if __name__ == '__main__':
    create_flags()
    absl.app.run(setup)


