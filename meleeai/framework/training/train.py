import absl.flags

from meleeai.framework.emulator.offline import OfflineExecutor

class Train:

    def __init__(self):
        """Initializes the training module for Alfred.
        """
        # Global fields
        self._flags = absl.flags.FLAGS
        
        self._online = self._flags.live_emulation
        if not self._online:
            self._executor = OfflineExecutor()

    def feed_model(self, published_data : list):
        pass