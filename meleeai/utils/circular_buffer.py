from multiprocessing.shared_memory import SharedMemory

class CircularBuffer:
   """CircularBuffer implementation in Python"""
   def __init__(self, obj, size=100):
      """Initializes the buffer with size 100 elements.
      :param size: Size of the buffer.
      """
      assert(obj is not None)
      self.__size          = size
      self.__read_head     = 0
      self.__write_head    = 0

      self.__is_ahead      = True
      self.__has_written   = False

      self.__buffer        =


   def read(self):
      """Reads a position and returns an index off the buffer.
      :return: Integer
      """
      if not self.__has_written:
         raise IndexError('Buffer hasn\'t been written too yet.')

      tmp_read_head = self.__read_head

      self.__is_ahead = True
      future_read_head = (self.__read_head + 1) % self.__size
      if self.__has_written and future_read_head != self.__write_head:
         self.__read_head = future_read_head
      return tmp_read_head


   def write(self):
      """Writes data to the buffer. Returns the index of the current write.
      :return: Integer
      """
      tmp_write_head = self.__write_head

      self.__has_written = True
      future_write_head = (self.__write_head + 1) % self.__size
      if self.__write_head == self.__read_head and not self.__is_ahead:
         self.__read_head = self.__write_head = future_write_head
      else:
         if future_write_head == self.__read_head:
            self.__is_ahead = False
         self.__write_head = future_write_head
      return tmp_write_head