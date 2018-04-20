from random import randint
from uuid import uuid4


class Client(object):

    def __init__(self, address, name):
        self.address = address
        self.name = name


class Game(object):

    # ToDo описать здесь игровой сервер

    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.current_turn = [1, bool(randint(0, 1))]
        self.methods = {''}

    def process(self, data):
        pass

    def next_turn(self):
        self.current_turn[0] += 1

    def hand_turn(self):
        self.current_turn[1] = not self.current_turn[1]


class Processor(object):

    def __init__(self, limit=5):
        self.queue = list()
        self.methods = {'ready': self.on_ready,
                        'game': self.process_game
                        }
        self.games = dict()
        self.limit = limit

    def process(self, data, addr):
        func = self.methods[data['code']]
        result = func(data['data'], addr)
        response = {'code': 'ok', 'data': result}
        return response

    def on_ready(self, data, addr):
        client = Client(data['name'], addr)
        self.queue.append(client)

    def process_game(self, data, addr):
        game = self.games[data.pop('game_id')]
        game.process(data)

    def start_game(self):
        if len(self.games) < self.limit & len(self.queue) >= 2:
            player1 = self.queue.pop(0)
            player2 = self.queue.pop(0)
            game_id = uuid4()
            game = Game(player1, player2)
            self.games.update({game_id: game})
