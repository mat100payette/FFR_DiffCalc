from enum import Enum
from typing import List, NamedTuple


class SongInfo(NamedTuple):
    '''Represents a minimal tuple of the necessary song info.'''
    level: int
    name: str
    difficulty: int

class NoteDirection(str, Enum):
    '''Enum of possible `FFRNote` direction values'''
    LEFT = 'L'
    DOWN = 'D'
    UP = 'U'
    RIGHT = 'R'

class FFRNote(NamedTuple):
    '''Represents a note in a beatbox.'''
    direction: NoteDirection
    frame: int

class Chart:
    '''Represents a FFR chart with its basic info and its notes.'''
    info: SongInfo
    beatbox: List[FFRNote]

    def __init__(self, info: SongInfo, beatbox: List[FFRNote]):
        self.info = info
        self.beatbox = beatbox