import json

from models import Chart, FFRNote, SongInfo

class ChartEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Chart):
            return [self.default(obj.info), self.default(obj.beatbox)]

        if isinstance(obj, SongInfo):
            return [obj.level, obj.name, obj.difficulty]

        if isinstance(obj, FFRNote):
            return [obj.direction.value, obj.frame]

        if isinstance(obj, list):
            return [self.default(item) for item in obj]
            
        raise Exception(f'Invalid Chart object. Value of type {type(obj)} ({obj}) encountered.')
