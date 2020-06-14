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

class CommandType(Enum):

    UPDATE = 0,
    SHUTDOWN = 1

class StreamFrame:

    def __init__(self, video_queue_in, video_queue_out):
        self._video_queue_in = video_queue_in
        self._video_queue_out = video_queue_out


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
            if payload[0] == CommandType.UPDATE:
                self.draw_frame(np.array(Image.open(BytesIO(payload[1]))))
                self.canvas.draw()
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