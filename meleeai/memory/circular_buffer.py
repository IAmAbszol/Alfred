import numpy as np

from multiprocessing import shared_memory, Lock

class CircularBuffer:
   """CircularBuffer implementation in Python"""
   def __init__(self, obj, shared_memory_name=None, size=100):
      """Initializes the buffer with size 100 elements.
      :param shared_memory_name: Name of the shared_memory, if None then create.
      :param size: Size of the buffer.
      """
      assert obj is not None, 'Object cannot be None.'
      self.__size          = size
      self.__read_head     = 0
      self.__write_head    = 0

      self.__is_ahead      = True
      self.__has_written   = False

      self.__obj           = type(obj)
      self.__lock          = Lock()
      self.__array         = np.ones(shape=(size), dtype=object)
      self.__shm_obj       = shared_memory.SharedMemory(create=True, size=self.__array.nbytes) \
                                 if not shared_memory_name else shared_memory.SharedMemory(name=shared_memory_name, size=self.__array.nbytes)
      self.__buffer        = np.ndarray(shape=(self.__array.shape), buffer=self.__shm_obj.buf, dtype=object)
      self.__buffer[:]     = self.__array[:]


   def __del__(self):
      self.__shm_obj.close()
      self.__shm_obj.unlink()


   def get_obj(self):
      return self.__obj


   def get_name(self):
      """Gets the name of the shared_memory instance.
      :return: String
      """
      return self.__shm_obj.name


   def read(self):
      """Reads a position and returns an index off the buffer.
      :return: Integer, object
      """
      if not self.__has_written:
         raise IndexError('Buffer hasn\'t been written too yet.')

      read_head_index = self.__read_head

      self.__is_ahead = True
      future_read_head = (self.__read_head + 1) % self.__size
      if self.__has_written and future_read_head != self.__write_head:
         self.__read_head = future_read_head
      with self.__lock:
         return read_head_index, self.__buffer[read_head_index]


   def write(self, obj):
      """Writes data to the buffer. Returns the index of the current write.
      :param obj: Object to insert into list.
      :return: Integer
      """
      assert isinstance(obj, self.__obj), f'Expected object of type {self.__obj}, received type {type(obj)}.'
      write_head_index = self.__write_head

      self.__has_written = True
      future_write_head = (self.__write_head + 1) % self.__size
      if self.__write_head == self.__read_head and not self.__is_ahead:
         self.__read_head = self.__write_head = future_write_head
      else:
         if future_write_head == self.__read_head:
            self.__is_ahead = False
         self.__write_head = future_write_head
      with self.__lock:
         self.__buffer[write_head_index] = obj
         return write_head_index