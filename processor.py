from random import randint


class Client(object):

    def __init__(self, address, name):
        self.address = address
        self.name = name


class Game(object):

    def __init__(self, player1, player2):
        self.players = {'player1': player1,
                        'player2': player2}
        self.current_turn = [1, randint(0, 1)]


class Processor(object):

    def __init__(self, limit=5):
        self.queue = list()
        self.methods = {'ready': self.on_ready,
                        'game': self.process_game
                        }
        self.games = list()
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
        pass

    def start_game(self):
        if len(self.games) < self.limit & len(self.queue) >= 2:
            player1 = self.queue.pop(0)
            player2 = self.queue.pop(0)
            game = Game(player1, player2)
            self.games.append(game)
