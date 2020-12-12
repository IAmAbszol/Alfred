import absl.flags
import logging
import sys

from gc import get_referents
from types import ModuleType, FunctionType

import slippi

from slippi.game import Game

BLACKLIST = type, ModuleType, FunctionType

# Stackoverflow: https://stackoverflow.com/a/30316760/10292238
def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('getsize() does not take argument of type: '+ str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size

def should_play(slippi_file):
    """Determines whether the criterion to run has been met.
    :param slippi_file: Absolute path to .slp file for replay.
    :return: Tuple [-1 == Not a match, first index is observable player.]
    """
    flags = absl.flags.FLAGS
    slippi_port = -1
    opponent_port = -1

    try:
        slippi_game = Game(slippi_file)

        slippi_version = tuple(list(map(int, str(slippi_game.start.slippi.version).split('.'))))
        if slippi_version >= tuple(list(map(int, flags.min_slippi_version.split('.')))):
            if slippi_version >= (2,0,0):
                if len(slippi_game.frames) >= flags.min_frame_length:
                    if flags.no_lras:
                        if slippi_game.end and slippi_game.end.lras_initiator:
                            return (slippi_port, opponent_port)
                    start_frame = slippi_game.start.__dict__
                    if not start_frame['is_teams'] and start_frame['stage'] == flags.stage_id:
                        ports = [-1, -1]
                        for player_index, player in enumerate(start_frame['players'], start=1):
                            if player is None:
                                continue
                            player_dict = player.__dict__
                            if player_dict['character'] == flags.player_character_id and \
                                    player_dict['costume'] == flags.player_costume_id:
                                ports[0] = player_index
                            elif player_dict['character'] == flags.opponent_character_id:
                                ports[1] = player_index
                        if not any(ports):
                            slippi_port, opponent_port = [-1, -1]
                        else:
                            slippi_port, opponent_port = ports
    except slippi.parse.ParseError as pe:
        logging.error(f'Received parsing error: {pe}.')
    return slippi_port, opponent_port