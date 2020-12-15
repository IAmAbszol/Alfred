import absl.flags

from meleeai.memory.circular_buffer import CircularBuffer

class Memory:

   __instance = None

   def __init__(self):
      """Singleton instance of the Memory object.
      """
      self._flags          = absl.flags.FLAGS

      self.__size          = self._flags.memorysize
      self.__objects       = set()
      self.__memory_dict   = {}


   def __new__(cls):
      if cls.__instance is None:
         cls.__instance = super(Memory, cls).__new__(cls)
      return cls.__instance


   def __str__(self):
      return f'Memory instance, contains {self.__memory_dict} entries.'


   def writeit(self, x):
      self._test_dict[x] = 'hello'
      return self._test_dict

   def create(self, obj, name=None):
      """Creates a CircularBuffer for the object.
      Will not insert upon creation, use write(...).
      :param obj: Object Circularbuffer should represent.
      :param name: Name of the SharedMemory to connect to.
      :return: Tuple(name, CircularBuffer)
      """
      if type(obj) not in self.__objects:
         circular_buffer = CircularBuffer(obj, shared_memory_name=name, size=self.__size)
         self.__memory_dict[circular_buffer.get_name()] = circular_buffer
         self.__objects.add(type(obj))
         return (circular_buffer.get_name(), circular_buffer)


   def lookup_object(self, obj):
      """Finds the name and buffer associated with the dictionary.
      :param obj: Object to look up.
      :return: Tuple (name, CircularBuffer)
      """
      if type(obj) in self.__objects:
         for name, circular_buffer in self.__memory_dict.items():
            if circular_buffer.get_obj() == type(obj):
               return (name, circular_buffer)


   def read_memory(self, name):
      """Reads the mapped shared_memory to the set name.
      :param name: Name of shared_memory instance.
      :throws: KeyError when attempting to access memory that hasn't been set
               aside yet.
      :return: object
      """
      if name not in self.__memory_dict:
         raise KeyError(f'No such key entry found {name}, initialize first.')
      return self.__memory_dict[name].read()


   def write_memory(self, obj, name=None):
      """Writes the object to its respective memory slot,
      creating said object if it doesn't exist. Its the users
      responsibilty to monitor objects coming in.
      :param obj: Object to write as key to CircularBuffer.
      :return: Tuple(name, circular_buffer)
      """
      if type(obj) not in self.__objects:
         name, circular_buffer = self.create(obj)
      elif name is not None:
         if name not in self.__memory_dict:
            raise KeyError(f'No such key entry found {name}, initialize first.')
         else:
            circular_buffer = self.__memory_dict[name]
      else:
         name, circular_buffer = self.lookup_object(obj)
      circular_buffer.write(obj)
      return (name, circular_buffer)
