from gym.envs.registration import register
from importlib_metadata import PackageNotFoundError, version

#try:
#    __version__ == version('meleeai')
#except PackageNotFoundError:
#    __version__ = 'unknown'

register(
    id='basic-v0',
    entry_point='meleeai.envs:Basic',
)

