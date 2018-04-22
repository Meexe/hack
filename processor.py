from uuid import uuid4
import asyncio
from utils import *
from philologist import check_rhyme
from pymorphy2 import MorphAnalyzer


class ProcessorError(Exception):
    """Общий класс ошибок процессора"""
    pass


class Client(object):
    """
    Класс клиента
    """

    def __init__(self, addr, name, words):
        self.addr = addr
        self.name = name
        self.hp = 100
        self.words = words


class GameProtocol(asyncio.Protocol):
    """
    Класс для реализации обмена данных во время игры
    """

    def __init__(self, message, loop):
        self.message = message
        self.loop = loop

    def connection_made(self, transport):
        transport.write(to_json(self.message))
        self.loop.stop()


class Game(object):
    """
    Класс описывающий игру
    """

    def __init__(self, game_id, player1, player2):
        """
        При инициализации мы хотим, чтобы наши игроки знали другу о друге и игре
        """
        self.id = game_id
        self.player1 = player1
        self.player2 = player2

        data1 = {'name': self.player2.name, 'turn': False, 'game_id': game_id}
        data2 = {'name': self.player1.name, 'turn': True, 'game_id': game_id}

        message1 = {'code': 'start', 'data': data1}
        message2 = {'code': 'start', 'data': data2}

        self.send(message1, self.player1.addr)
        self.send(message2, self.player2.addr)

        self.turn = [1, False]
        self.string = ''
        self.time = None

    def process(self, data, morph):
        """
        Основной метод обработки хода игры
        """
        if not self.turn[1]:                # Ход первого игрока (придумывание строки)
            self.hand_turn()

            self.string = data['string']
            self.validate(morph)
            self.time = data['time']
            self.send(self.string, self.player2.addr)

        else:                               # Ход второго игрока (рифмование строки)
            self.next_turn()

            rhyme = data['string']
            damage = check_rhyme(self.string['string'], rhyme, self.time, data['time'])
            self.player1.hp -= damage

            message = {'string': rhyme, 'dmg': damage, 'turn': self.turn}
            self.send(message, self.player1)
            self.send(message, self.player2)

            if self.player1.hp <= 0:
                processor.stop_game(self.id)
                return

            self.player1, self.player2 = self.player2, self.player1
        return None

    def next_turn(self):
        """
        Метод переключает ход на следущий раунд
        """
        self.turn[0] += 1
        self.hand_turn()

    def hand_turn(self):
        """
        Метод передает ход другому игроку
        """
        self.turn[1] = not self.turn[1]

    @staticmethod
    def send(message, addr):
        """
        Метод рассылает по протоколу GameProtocol адресатам сообщения
        """
        request = {'code': 'game', 'data': message}
        request = to_json(request)
        loop = asyncio.get_event_loop()
        coro = loop.create_connection(lambda: GameProtocol(request, loop), addr)
        loop.run_until_complete(coro)
        loop.run_forever()
        loop.close()

    def validate(self, morph):
        """
        Метод проверяет, использовал ли клиент допустимые слова
        """
        words = self.string.strip(punctuation).split()
        for word in words:
            if morph.parse(word)[0].normal_form not in self.player1.words:
                return False
        return True


class Processor(object):
    """
    Класс обработки данных
    """

    morph = MorphAnalyzer()                         # Жрет много памяти, делаем один на много процессоров

    def __init__(self, limit=5):
        self.queue = list()
        self.methods = {'ready': self.on_ready,
                        'game': self.process_game
                        }
        self.games = dict()
        self.limit = limit

    def process(self, data, addr):
        """Метод, вызывающий другие методы и передающий туда данные"""
        try:
            func = self.methods[data['code']]
        except KeyError:
            raise ProcessorError('no code')

        except TypeError:
            raise ProcessorError('bad request')

        result = func(data['data'], addr)
        response = {'code': 'ok', 'data': result}
        return response

    def on_ready(self, data, addr):
        """Постановка нового клиента в очередь"""
        if data['name'] == 'nickname':
            name = uuid4()
        else:
            name = data['name']

        words = []
        for word in data['words']:
            words.append(self.morph.parse(word)[0].normal_form)

        client = Client(name, addr, words)
        self.queue.append(client)
        self.start_game()

    def process_game(self, data, addr):
        """
        Методы, передающий данные в объект класса Game
        """
        game = self.games[data.pop('game_id')]
        return game.process(data, self.morph)

    def start_game(self):
        """
        Старт новой игры
        Метод вызывается в двух случаях: новый клиент встал в очередь или закончилась старая игра
        """
        if len(self.games) < self.limit & len(self.queue) >= 2:
            player1 = self.queue.pop(0)
            player2 = self.queue.pop(0)
            game_id = uuid4()
            game = Game(game_id, player1, player2)
            self.games.update({game_id: game})

    def stop_game(self, game_id):
        """
        Конец игры, методы вызывается только из объекта класса Game
        """
        self.games.pop(game_id)
        self.start_game()


processor = Processor()
