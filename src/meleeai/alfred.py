import argparse
import datetime
import logging
import os

from meleeai.framework.engine import Engine

FORMAT = '(%(asctime)s) [%(filename)s:%(lineno)s - %(funcName)20s() ] [%(levelname)s] %(message)s'

def main():
    parser = argparse.ArgumentParser(description='Alfred The Melee AI')
    parser.add_argument('-d', '--display', required=False, action='store_true', help='Display Alfred, helpful when sending/receiving on a separate node.')
    parser.add_argument('-r', '--run', required=False, action='store_true', help='Run Alfred, uses the configuration file generated for the model location.')
    parser.add_argument('-t', '--train', required=False, action='store_true', help='Trains Alfred provided a particular dataset of sequential images paired against Slippi data loaded by the config.')
    parser.add_argument('-c', '--config', default=None, action='store', type=str, help='Configuration file location, if none is provided then use Alfred default.')
    args = parser.parse_args()

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
    
    with Engine(display=args.display, predict=args.run, train=args.train) as engine:
        engine.main()

if __name__ == '__main__':
    main()
    
    
