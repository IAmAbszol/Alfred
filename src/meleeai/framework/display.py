"""
    Matplotlib cannot exist in a separate thread, to go about this, a separate
    process is queue'd off. This process is connected via Engine's multiprocessing.queue.
"""

import numpy as np
import queue
import sys
import time

import matplotlib
matplotlib.use('TkAgg')

from matplotlib import animation
from matplotlib import ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from tkinter import * # TODO: A sin has been committed, fix later

from enum import Enum
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw

from slippi.event import Frame, Start, End

class CommandType(Enum):

    VIDEO_UPDATE    = 0,
    SLIPPI_UPDATE   = 1,
    SHUTDOWN        = 2

class StreamFrame:

    def __init__(self, video_queue_in, video_queue_out):
        self._video_queue_in = video_queue_in
        self._video_queue_out = video_queue_out

        # Slippi viewable data
        #self.


    #def _extract_

    def _on_close(self):
        self._video_queue_out.put_nowait((CommandType.SHUTDOWN, None))
        self.window.destroy()
    

    def initialize(self):
        self.window.protocol('WM_DELETE_WINDOW', self._on_close)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas.draw()
        self.canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=True)


    def collect_frame(self):
        try:
            payload = self._video_queue_in.get_nowait()
            if payload[0] == CommandType.VIDEO_UPDATE:
                self.draw_frame(np.array(Image.open(BytesIO(payload[1]))))
                self.canvas.draw()
            if payload[0] == CommandType.SLIPPI_UPDATE:
                event = payload[1]
                # TODO: Extract and store specific information for the display. 
                #       Debating on making a utils toolset to get map, etc.
                #       Another idea is to have some sort of singleton that has an updater
                #       which updates with the slippi data coming in. Then this would have
                #       a ton get getters for specific info.
                if isinstance(event, Start):
                    print(event)
                elif isinstance(event, Frame.Event.Type.PRE):
                    pass
                elif isinstance(event, Frame.Event.Type.POST):
                    pass
                elif isinstance(event, End):
                    pass
            elif payload[0] == CommandType.SHUTDOWN:
                self.window.destroy()
        except queue.Empty:
            pass
        self.window.after(1, self.collect_frame)


    def draw_frame(self, image):
        if not hasattr(self, 'stream_image'):
            self.stream_image = self.ax.imshow(image)
        else:                
            self.stream_image.set_data(image)

    def run(self):
        self.window = Tk()
        self.window.title('Stream')
        self.initialize()
        self.collect_frame()
        self.window.update()
        self.window.deiconify()
        self.window.mainloop()