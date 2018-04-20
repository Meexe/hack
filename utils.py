from json import loads, dumps


def to_json(string):
    return dumps(string).encode('utf-8')


def from_json(string):
    return loads(string.decode('utf-8'))
