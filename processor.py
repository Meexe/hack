from uuid import uuid4
import asyncio
from utils import *
from philologist import check_rhyme


class Client(object):

    def __init__(self, addr, name, words):
        self.addr = addr
        self.name = name
        self.hp = 100
        self.words = words


class DataTcpProtocol(asyncio.Protocol):

    def __init__(self, message, loop):
        self.message = message
        self.loop = loop

    def connection_made(self, transport):
        transport.write(to_json(self.message))
        self.loop.stop()


class Game(object):

    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2

        data1 = {'name': self.player2.name, 'turn': False}
        data2 = {'name': self.player1.name, 'turn': True}

        message1 = {'code': 'start', 'data': data1}
        message2 = {'code': 'start', 'data': data2}

        self.send(message1, self.player1.addr)
        self.send(message2, self.player2.addr)
        self.turn = [1, False]
        self.methods = {''}
        self.string = ''
        self.time = None

    def process(self, data):
        if not data['turn']:
            self.hand_turn()

            self.string = data['string']
            self.validate(self.string)
            self.time = data['time']
            self.send(self.string, self.player2.addr)

        else:
            self.next_turn()
            self.hand_turn()

            rhyme = data['string']
            damage = check_rhyme(self.string['string'], rhyme, self.time, data['time'])
            self.player1.hp -= damage

            if self.player1.hp <= 0:
                message = {'code': 'win', 'data': {'winner': self.player2.name}}
                self.send(message, self.player1.addr)
                self.send(message, self.player2.addr)

            message = {'string': rhyme, 'dmg': damage, 'turn': self.turn}
            self.send(message, self.player1)
            self.send(message, self.player2)

            self.player1, self.player2 = self.player2, self.player1

    def next_turn(self):
        self.turn[0] += 1

    def hand_turn(self):
        self.turn[1] = not self.turn[1]

    @staticmethod
    def send(message, addr):
        request = {'code': 'game', 'data': message}
        request = to_json(request)
        loop = asyncio.get_event_loop()
        coro = loop.create_connection(lambda: DataTcpProtocol(request, loop), addr)
        loop.run_until_complete(coro)
        loop.run_forever()
        loop.close()

    def validate(self):
        pass


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
        if data['name'] == 'nickname':
            name = uuid4()
        else:
            name = data['name']

        words = data['words']

        client = Client(name, addr, words)
        self.queue.append(client)
        self.start_game()

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
