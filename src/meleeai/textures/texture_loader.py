import glob
import os

from PIL import Image

class TextureLoader:
    """TextureLoader"""
    _instance = None

    class _TextureSingleton:
        """_TextureSingleton"""

        def __init__(self):
            """Initializes the texture singleton"""
            self._textures = self.load()


        def load(self):
            """Loads the available .png's within the active script directory"""
            return dict(
                        [(os.path.split(x)[1].replace('.png', ''), Image.open(x)) for x in glob.glob(
                           os.path.join(os.path.dirname(os.path.realpath(__file__)), '**', '*.png'), recursive=True)]
                    )


    def __init__(self):
        """Initializes the texture loader"""
        if TextureLoader._instance is None:
            TextureLoader._instance = TextureLoader._TextureSingleton()


def get_textures():
    """Gathers the textures loaded"""
    return TextureLoader()._instance._textures

