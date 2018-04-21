import asyncio
from processor import Processor
from utils import *
from json import JSONDecodeError


class ServerError(Exception):
    pass


class BadRequest(ServerError):
    pass


class EchoServerClientProtocol(asyncio.Protocol):
    """Класс для реализции сервера при помощи asyncio"""

    processor = Processor()

    def __init__(self):
        super().__init__()
        self._buffer = b''

    def process(self, data, addr):
        """Обработка входной команды сервера"""
        response = {'code': 'ok',
                    'data': self.processor.process(data, addr)}
        return response

    def connection_made(self, transport):
        self.transport = transport
        self.addr = transport.get_extra_info('peername')

    def data_received(self, data):
        """Метод data_received вызывается при получении данных в сокете"""
        self._buffer += data

        try:
            decoded_data = from_json(self._buffer)

        except (UnicodeDecodeError, JSONDecodeError) as err:
            raise BadRequest(err)

        self._buffer = b''

        print(f'Got {decoded_data} from {self.addr}')

        response = self.process(decoded_data, self.addr)

        print(f'Sending {response}')

        self.transport.write(to_json(response))

        self.transport.close()


def run_server(host, port):
    print(f'Starting server on {host}:{port}')
    loop = asyncio.get_event_loop()
    coro = loop.create_server(
        EchoServerClientProtocol,
        host, port
    )
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
    run_server('192.168.100.185', 8888)
