"""
    Matplotlib cannot exist in a separate thread, to go about this, a separate
    process is queue'd off. This process is connected via Engine's multiprocessing.queue.
"""

import logging
import numpy as np
import queue
import sys
import time

from tkinter import * # TODO: A sin has been committed, fix later
from slippi.event import Buttons, Frame, Start, End

from enum import Enum
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw, ImageTk
from tkinter import Toplevel, Label, Tk

from meleeai.textures.draw_controller import ControllerLayout
from meleeai.textures.texture_loader import get_textures
from meleeai.utils.message_type import MessageType


class StreamFrame:
    """StreamFrame"""
    def __init__(self, video_queue_in, video_queue_out):
        """Initializes the StreamFrame object
        :param video_queue_in: Commands such as Video, Slippi, and Shutdown are passed through to here
        :param video_queue_out: Commands such as Shutdown to notify the parent caller
        """
        self.controller_drawer = ControllerLayout()

        self._video_queue_in = video_queue_in
        self._video_queue_out = video_queue_out

        self._spawned_controllers = {}

    def _on_close(self):
        """Close this instance for process to parent"""
        self._video_queue_out.put_nowait((MessageType.SHUTDOWN, None))
        self.window.destroy()


    def initialize(self):
        """Initializes the view for StreamFrame"""
        self.window.protocol('WM_DELETE_WINDOW', self._on_close)

        self.image_label = Label(master=self.window)
        self.image_label.pack(side="bottom", fill="both", expand="yes")

        for port in range(4):
            self._spawned_controllers[port] = Label(master=self.window)
            self._spawned_controllers[port].pack(side="bottom", fill="both", expand="no")

    def collect(self):
        """Collects data off the video_queue_in and handles it appropriately"""
        try:
            payload = self._video_queue_in.get_nowait()
            if payload[0] == MessageType.VIDEO:
                #video_image = ImageTk.PhotoImage(Image.open(BytesIO(payload[1])))
                #self.image_label.configure(image=video_image)
                #self.image_label.image = video_image
                pass
            if payload[0] == MessageType.SLIPPI:
                event = payload[1]
                # Run through the available ports
                # TODO: Change to point at the tuples port
                for port in range(4):
                    if port == 0:
                        #if isinstance(event, tuple):
                        #    print(event[0])
                        canvas = self.controller_drawer.draw_controller_overlay(event, port)
                        if canvas:
                            controller_image = ImageTk.PhotoImage(canvas)
                            self._spawned_controllers[port].configure(image=controller_image)
                            self._spawned_controllers[port].image = controller_image
            elif payload[0] == MessageType.SHUTDOWN:
                self.window.destroy()
        except queue.Empty:
            pass
        except TclError:
            self._on_close()
        except Exception as e:
            logging.error(e)

        self.window.update()
        self.window.after(1, self.collect)


    def setup(self):
        """Setup for StreamFrame"""
        self.window = Tk()
        self.window.title('Alfred Display')
        self.initialize()
        self.collect()
        self.window.mainloop()


if __name__ == '__main__':
    """
    cd = ControllerLayout()

    import time
    from meleeai.utils.slippi_parser import SlippiParser
    slippi_parser = SlippiParser()
    events = slippi_parser.parse_bin('Game.slp', network=False)

    from slippi.event import Buttons, Frame, Start, End
    for idx, event in enumerate(events):
        canvas = cd.draw_controller_overlay(event, 0)
        if canvas:
            canvas.save('D:\\Documents\\Projects\\MeleeAI\\src\\meleeai\\textures\\tmp\\{}.png'.format(idx), 'PNG')
            exit(0)
    """
    import time
    import threading
    from meleeai.utils.slippi_parser import SlippiParser
    slippi_parser = SlippiParser()
    events = slippi_parser.parse_bin('Game.slp', network=False)
    video_queue_in = queue.Queue()
    video_queue_out = queue.Queue()
    print(len(events))
    def thread_func():
        for (timestamp, event) in events:
            video_queue_in.put((MessageType.SLIPPI, event))

    tf = threading.Thread(target=thread_func)
    tf.start()
    tf.join()
    sf = StreamFrame(video_queue_in, video_queue_out)
    sf.setup()
