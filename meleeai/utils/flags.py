import absl.flags
import os


FLAGS = absl.flags.FLAGS


def create_flags():
    """Creates the flags"""
    flags = absl.flags
    
    flags.DEFINE_integer('display_queuesize', 10, 'Queue size regarding the display gui.')
    flags.DEFINE_integer('controllerport', 55079, 'Controller port sending to Alfred.')
    flags.DEFINE_integer('slippiport', 55080, 'Slippi port sending to Alfred.')
    flags.DEFINE_integer('videoport', 55081, 'Video port sending to Alfrd.')
    flags.DEFINE_integer('receiverbuffer', 100, 'Buffer data to hold till consumed.')
    flags.DEFINE_integer('slippi_start_byte', 418, 'Start byte (54) for slippi start data.')
    flags.DEFINE_integer('slippi_pre_byte', 64, 'Pre frame byte (55) for pre-frame data.')
    flags.DEFINE_integer('slippi_post_byte', 52, 'Post frame byte (56) for post-frame data.')
    flags.DEFINE_integer('slippi_end_byte', 2, 'End byte (57) for slippi end data.')
    flags.DEFINE_float('prediction_tick_rate', .016, '1/60th of a frame at which a prediction should occur.')
    flags.DEFINE_integer('alfred_port', 1, 'Alfred port that\'s dedicated to the agent.')
    flags.DEFINE_integer('gc_ports', 4, 'Number of gamecube ports on the system.')
    flags.DEFINE_bool('live_emulation', False, 'If the training for alfred should be conducted on a live session.')
    flags.DEFINE_string('emulator', './Ishiiruka/bin/Dolphin.exe' if os.name == 'nt' else './Ishiiruka/bin/dolphin', 'Alfred Ishiiruka Slippi emulator with socket implementation. Playback MUST be setup if this choice is used.')
    flags.DEFINE_integer('min_frame_length', 1500, 'Minimum frame length required to run the emulation.')
    flags.DEFINE_bool('no_lras', True, 'Ignore slippi recordings that end with LRA+START.')
    flags.DEFINE_integer('burnouttime', 10000, 'Time to wait until offline emulation has completed a slippi playback. Used when End frame is either missed, dropped, or merely not sent.')
    flags.DEFINE_bool('display', False, 'Displays Alfred\'s GUI.')
    flags.DEFINE_bool('train', False, 'Runs the training part of the engine.')
    flags.DEFINE_string('slippi_data', './data/', 'Slippi data to run the emulator ontop of if offline.')

    # Since replays can have different ports, names, etc associated
    # we'll sort by character name, stage and color.
    flags.DEFINE_integer('player_character_id', 0, 'Character ID associated by Slippi, view slippi.id.CSSCharacter for more details.')
    flags.DEFINE_integer('player_costume_id', 4, 'Costume ID associated by Slippi (0 = Default).')
    flags.DEFINE_integer('opponent_character_id', 20, 'Character ID associated by Slippi, view slippi.id.CSSCharacter for more details.')
    flags.DEFINE_integer('stage_id', 31, 'Stage ID associated by Slippi, view slippi.id.Stage for more details.')
    flags.DEFINE_string('min_slippi_version', '2.0.0', 'Minimum slippi version able to be parsed.')