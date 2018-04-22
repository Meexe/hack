import asyncio
from processor import processor, ProcessorError
from utils import *
from json import JSONDecodeError


class ServerError(Exception):
    """Общий класс ошибок сервера"""
    pass


class BadRequest(ServerError):
    """Неправильный формат запроса"""
    pass


class Server(asyncio.Protocol):
    """Класс для реализции сервера при помощи asyncio"""

    def __init__(self):
        super().__init__()
        self._buffer = b''

    @staticmethod
    def process(data, addr):
        """Обработка запросов перенаправляется в класс Processor"""
        response = processor.process(data, addr)
        return response

    def connection_made(self, transport):
        """Метод connection_made вызывается при открытии нового подключения"""
        self.transport = transport
        self.addr = transport.get_extra_info('peername')
        print(f'Connection from {self.addr}')

    def data_received(self, data):
        """Метод data_received вызывается при получении данных в сокете"""
        self._buffer += data

        try:
            request = from_json(self._buffer)

        except (UnicodeDecodeError, JSONDecodeError) as err:
            response = {'code': 'error',
                        'data': str(err)}
            print(f'Sending {response}')
            self.transport.write(to_json(response))
            self.transport.close()
            return


        self._buffer = b''

        print(f'Got {request}')

        if request == 'ping':
            response = 'pong'

        else:
            try:
                response = self.process(request, self.addr)

            except ProcessorError as err:
                response = {'code': 'error',
                            'data': str(err)}

        print(f'Sending {response}')
        self.transport.write(to_json(response))
        self.transport.close()


def run_server(host, port):
    print(f'Starting server on {host}:{port}')
    loop = asyncio.get_event_loop()
    coro = loop.create_server(Server, host, port)
    server = loop.run_until_complete(coro)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
    print('\nClosing server')


if __name__ == "__main__":
    run_server('172.20.10.13', 8888)
