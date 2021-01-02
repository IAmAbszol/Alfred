import struct

class ControllerParser:
   """Controller Parser"""

   CONTROLLER_BIN_STRING = 'I I I H B B B B B B B B B'
   CONTROLLER_BIN_SIZE = struct.calcsize(CONTROLLER_BIN_STRING)
   UNPACK_CONTROLLER = struct.Struct(CONTROLLER_BIN_STRING).unpack

   def template(self,
               device_number,
               timestamp_sec,
               timestamp_micro,
               button,
               stickX,
               stickY,
               substickX,
               substickY,
               triggerLeft,
               triggerRight,
               analogA,
               analogB,
               err):
      return {
         'device_number': device_number,
         'timestamp_sec': timestamp_sec,
         'timestamp_micro': timestamp_micro,
         'button': button,
         'stickX': stickX,
         'stickY': stickY,
         'substickX': substickX,
         'substickY': substickY,
         'triggerLeft': triggerLeft,
         'triggerRight': triggerRight,
         'analogA': analogA,
         'analogB': analogB,
         'err': err
      }

   def parse_bin(self, data):
      """Parses the controller data.
      :param data: Controller data string from the socket.
      :return: Dictionary
      """
      return self.template(*self.UNPACK_CONTROLLER(data))

   def parse_list(self, data_list):
      """Parses the list of controller data.
      :param data_list: 1xN elements, N = # of keys in template.
      :return: Dictionary
      """
      return self.template(*data_list)