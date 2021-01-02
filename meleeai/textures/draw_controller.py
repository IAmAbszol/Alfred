import numpy as np

from PIL import Image, ImageDraw, ImageFont

from meleeai.textures.texture_loader import get_textures
from slippi.event import Buttons, Frame, Start, End


class ControllerLayout:
    """ControllerLayout"""
    def __init__(self):
        """Initializes the ControllerLayout class"""
        self._BUTTONS = {
            'START': Buttons.Logical.START,
            'Y': Buttons.Logical.Y,
            'X': Buttons.Logical.X,
            'B': Buttons.Logical.B,
            'A': Buttons.Logical.A,
            'L': Buttons.Logical.L,
            'R': Buttons.Logical.R,
            'Z': Buttons.Logical.Z,
            'DPAD_LEFT': Buttons.Logical.DPAD_LEFT,
            'DPAD_RIGHT': Buttons.Logical.DPAD_RIGHT,
            'DPAD_DOWN': Buttons.Logical.DPAD_DOWN,
            'DPAD_UP': Buttons.Logical.DPAD_UP
        }
        self._BUTTON_TEXTURES = {
            'DPAD': {
                'GATE': get_textures()['d-pad-gate'],
                'COLOR': (255, 255, 255, 255),
                'POSITION': {
                    'x': 100,
                    'y': 128
                }
            },
            'DPAD_LEFT': {
                'PRESSED': get_textures()['d-pad-pressed-left'],
                'COLOR': (255, 255, 255, 255),
                'POSITION': {
                    'x': 108,
                    'y': 144,
                },
            },
            'DPAD_RIGHT': {
                'PRESSED': get_textures()['d-pad-pressed-right'],
                'COLOR': (255, 255, 255, 255),
                'POSITION': {
                    'x': 108,
                    'y': 144,
                },
            },
            'DPAD_UP': {
                'PRESSED': get_textures()['d-pad-pressed-up'],
                'COLOR': (255, 255, 255, 255),
                'POSITION': {
                    'x': 108,
                    'y': 144,
                },
            },
            'DPAD_DOWN': {
                'PRESSED': get_textures()['d-pad-pressed-down'],
                'COLOR': (255, 255, 255, 255),
                'POSITION': {
                    'x': 108,
                    'y': 144,
                },
            },
            'JOYSTICK': {
                'GATE': get_textures()['joystick-gate'],
                'MASK': get_textures()['joystick-mask'],
                'STICK': get_textures()['joystick-outline'],
            },
            'CSTICK': {
                'GATE': get_textures()['c-stick-gate'],
                'STICK': get_textures()['c-stick'],
            },
            'A': {
                'OUTLINE': get_textures()['a-outline'],
                'PRESSED': get_textures()['a-pressed'],
                'COLOR': (0, 225, 150, 255),
                'POSITION': {
                    'x': 332,
                    'y': 48
                }
            },
            'B': {
                'OUTLINE': get_textures()['b-outline'],
                'PRESSED': get_textures()['b-pressed'],
                'COLOR': (230, 0, 0, 255),
                'POSITION': {
                    'x': 272,
                    'y': 92
                }
            },
            'X': {
                'OUTLINE': get_textures()['x-outline'],
                'PRESSED': get_textures()['x-pressed'],
                'COLOR': (255, 255, 255, 255),
                'POSITION': {
                    'x': 394,
                    'y': 32
                }
            },
            'Y': {
                'OUTLINE': get_textures()['y-outline'],
                'PRESSED': get_textures()['y-pressed'],
                'COLOR': (255, 255, 255, 255),
                'POSITION': {
                    'x': 316,
                    'y': -16
                }
            },
            'Z': {
                'OUTLINE': get_textures()['z-outline'],
                'PRESSED': get_textures()['z-pressed'],
                'COLOR': (165, 75, 165, 255),
                'POSITION': {
                    'x': 384,
                    'y': -32
                }
            },
            'START': {
                'OUTLINE': get_textures()['start-outline'],
                'PRESSED': get_textures()['start-pressed'],
                'COLOR': (255, 255, 255, 255),
                'POSITION': {
                    'x': 256,
                    'y': 26
                }
            }
        }

    def _change_color(self, texture, target_color):
        """Changes the color of the texture to the complete targeted color, except for transparent areas.
        :param texture: Image to be changed.
        :param target_color: Tuple RGBA for the intended color.
        """
        if texture:
            assert len(target_color) == 4, logging.error('Target color must have 4 channels, RGBA.')
            assert len(texture.getpixel((0,0))) == 4, logging.error('Texture must have 4 channels, RGBA')
            for w in range(texture.width):
                for h in range(texture.height):
                    r,g,b,a = texture.getpixel((w, h))
                    if (r,g,b,a) == (255,255,255,255):
                        texture.putpixel((w, h), target_color)

    def _draw_buttons(self, canvas, buttons):
        """Draw buttons onto the display according to the value passed and outlines needed.
        :param canvas: Controller canvas the buttons will be drawn on.
        :param buttons: Value retrieved by Slippi event indicating button combination pressed.
        """
        # Draw pressed buttons
        for button, mask in self._BUTTONS.items():
            if button in self._BUTTON_TEXTURES:
                texture_dict = self._BUTTON_TEXTURES[button]
                position = texture_dict['POSITION']
                if buttons & mask != Buttons.Logical.NONE:
                    texture = texture_dict['PRESSED'].resize((128, 128))
                elif 'OUTLINE' in texture_dict:
                    texture = texture_dict['OUTLINE'].resize((128, 128))
                else:
                    texture = None
                if texture:
                    self._change_color(texture, texture_dict['COLOR'])
                    canvas.paste(texture, (position['x'], position['y']), texture)
        # Draw d-pad-gate
        dpad_texture = self._BUTTON_TEXTURES['DPAD']
        self._change_color(texture, dpad_texture['COLOR'])
        canvas.paste(dpad_texture['GATE'].resize((128,128)), (dpad_texture['POSITION']['x'], dpad_texture['POSITION']['y']), dpad_texture['GATE'].resize((128,128)))


    def _draw_joystick(self, canvas, joystick_gate_string, joystick_canvas_string, joystick, gate_center=(0,0), image_width=128, color=(255,255,255,255)):
        """Draw joystick to canvas.
        :param canvas: Canvas to draw on, most accomodate dimensions provided
        :param joystick_gate_string: Gate for the joystick, string
        :param joystick_canvas_string: Joystick analog, string
        :param joystick: Joystick X, Y
        :param gate_center: Center location for the image gate
        :param image_width: Width of the image, width == height
        :param color: Color of the joystick
        """
        assert isinstance(gate_center, tuple) and len(gate_center) == 2, logging.error('gate_center must be tuple and of length 2, representing X, Y')
        center_x, center_y      = gate_center
        x, y                    = joystick.x, joystick.y
        vx, vy                  = x, 1 - y

        angle                   = np.arctan2(x, y)
        magnitude               = min(1, np.sqrt(x**2 + y**2))

        angle_cosine            = np.cos(angle)
        angle_sine              = np.sin(angle)

        # Calculate the end points
        offset_x                = (angle_cosine * image_width // 4 * magnitude) + center_x
        offset_y                = (angle_sine * image_width // 4 * magnitude) + center_y


        joystick_canvas = get_textures()[joystick_canvas_string].resize((image_width, image_width))
        joystick_gate = get_textures()[joystick_gate_string].resize((image_width, image_width))

        self._change_color(joystick_canvas, color)

        canvas.paste(joystick_gate, gate_center, joystick_gate)
        canvas.paste(joystick_canvas, (int(offset_x), int(offset_y)), joystick_canvas)

    def _draw_triggers(self, canvas, left_trigger, right_trigger):
        """Draw triggers for the controller.
        :param left_trigger: Left trigger value
        :param right_trigger: Right trigger value
        """
        trigger_canvas = ImageDraw.Draw(canvas)

        # Draw initial trigger line
        trigger_canvas.line((38, 16, 140, 16), fill=(255,255,255), width=12)
        trigger_canvas.line((192, 16, 294, 16), fill=(255,255,255), width=12)

        # Fill in black line with 1 - X where X = either trigger
        trigger_canvas.line((40, 16, 40 + 92 * (1 - left_trigger), 16), fill=(0,0,0), width=8)
        trigger_canvas.line((194, 16, 194 + 92 * (1 - right_trigger), 16), fill=(0,0,0), width=8)


    def draw_controller_overlay(self, event, port):
        """Draw controller overlay for specific instance
        :param event: Event tuple parsed by slippi
        :param port: Controller port to draw
        :return: Canvas else None
        """
        controller_canvas = None

        if isinstance(event, tuple) and len(event) == 3 and port == event[1] and isinstance(event[2], Frame.Port.Data.Pre):
            event_frame, event_port, main_event = event

            controller_canvas = Image.new(mode='RGBA', size=(480,240), color=(0,0,0))

            # Draw buttons
            self._draw_buttons(controller_canvas, main_event.buttons.logical.value)

            # Draw joystick
            self._draw_joystick(controller_canvas, 'joystick-gate', 'joystick-outline', main_event.joystick, (22, 52))

            # Draw c-stick
            self._draw_joystick(controller_canvas, 'c-stick-gate', 'c-stick', main_event.cstick, (176, 52), color=(255, 235, 0, 255))

            # Draw triggers
            self._draw_triggers(controller_canvas, main_event.triggers.physical.l, main_event.triggers.physical.r)

            # Draw text
            base_draw_canvas = ImageDraw.Draw(controller_canvas)
            base_draw_canvas.text((10,220), "Designed by bkacjios", fill=(255,255,255,128))
            base_draw_canvas.text((10,10), "Port - {}".format(port), fill=(255,255,255,128))

            return controller_canvas

if __name__ == '__main__':
    cd = ControllerLayout()

    import time
    from meleeai.utils.slippi_parser import SlippiParser
    slippi_parser = SlippiParser()
    events = slippi_parser.parse_bin('Game.slp', network=False)

    from slippi.event import Buttons, Frame, Start, End
    for idx, (timestamp, event) in enumerate(events):
        if idx == 300:
            print(event)
            canvas = cd.draw_controller_overlay(event, 0)
            if canvas:
                canvas.save('D:\\Documents\\Projects\\MeleeAI\\src\\meleeai\\textures\\tmp\\{}.png'.format(idx), 'PNG')