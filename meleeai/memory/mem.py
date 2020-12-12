from meleeai.memory.circular_buffer import CircularBuffer

class Memory:

   instance = None

   class _SingletonMemory:

      def __init__(self, memory_size):
         """Singleton instance of the Memory object.
         :param memory_size: Size to allocate per Circular Buffer.
         """
         self.__size          = memory_size
         self.__objects       = set()
         self.__memory_dict   = {}

      def __str__(self):
         return f'Memory instance, contains {len(self.__memory_dict)} entries.'


      def _create(self, obj):
         """Creates a CircularBuffer for the object.
         Will not insert upon creation, use write(...).
         :param obj: Object Circularbuffer should represent.
         :return: Tuple(name, CircularBuffer)
         """
         if type(obj) not in self.__objects:
            circular_buffer = CircularBuffer(obj, size=self.__size)
            self.__memory_dict[circular_buffer.get_name()] = circular_buffer
            return (circular_buffer.get_name(), circular_buffer)


      def lookup_object(self, obj):
         """Finds the name and buffer associated with the dictionary.
         :param obj: Object to look up.
         :return: Tuple (name, CircularBuffer)
         """
         print(self.__memory_dict)
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
            name, circular_buffer = self._create(obj)
         elif name is not None:
            if name not in self.__memory_dict:
               raise KeyError(f'No such key entry found {name}, initialize first.')
         else:
            name, circular_buffer = self.lookup_object(obj)
         self.__objects.add(type(obj))
         return (name, circular_buffer)


   def __init__(self, memory_size):
      if not Memory.instance:
         Memory.instance = Memory._SingletonMemory(memory_size)

def get_memory(memory_size=1000):
   if not Memory.instance:
      Memory.instance = Memory._SingletonMemory(memory_size)
   return Memory.instance