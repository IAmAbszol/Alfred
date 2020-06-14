from abc import ABC, abstractmethod

class ThreadRunner(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def stop(self):
        pass