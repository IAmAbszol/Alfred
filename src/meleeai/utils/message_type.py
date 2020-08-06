from enum import Enum

class MessageType(Enum):
    """Enum states for each type of data supported by Aflred"""
    CONTROLLER = 0,
    SLIPPI = 1,
    VIDEO = 2