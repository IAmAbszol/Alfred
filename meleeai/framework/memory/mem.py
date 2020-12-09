from multiprocessing import shared_memory, Lock

class Memory:

   def __init__(self, size=100):
      self._size           = size
      self._lock           = Lock()
      self._memory_map     = {}
      self._read_dict      = {}

   def __del__(self):
      for mem in self._memory_map.values():
         mem.close()
         mem.unlink()

   def initialize(self):
      """Initializes the memory for the specified object.
      :return: String, name of SharedMemory.
      """
      pass

   def insert(self, name, object):
      """SharedMemory is homogeneous and the type of the object will
      be used as the key to access said map.
      :param object: Object to insert into the map.
      """
      pass

   def read(self, name):
      pass


"""
   CASE #1
   DICT READ == MEM READ
   {x    : 2}
   x     = [2,5,2,3,4]
   Solution: (If MEM UPDATE): Update READ and MEM together by one. (If READ UPDATE): None.

   CASE #2
   DICT READ > MEM READ
   {x    : 3}
   x     = [2,5,2,3,4]
   Solution: Nothing to be done, don't read

   CASE #3
   DICT READ < MEM READ
   {x    : 1}
   x     = [2,5,2,3,4]
   Solution: Nothing to be done


   The DICT READ must never be overlapping the MEM READ position if it's already overlapped.
   In other words, if it's approaching on the LHS then it can never surpass the MEM READ pos.

"""
