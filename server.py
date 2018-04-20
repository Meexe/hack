import asyncio
from processor import Processor
from utils import *
from json import JSONDecodeError


class EchoServerClientProtocol(asyncio.Protocol):
    """Класс для реализции сервера при помощи asyncio"""

    # Обратите внимание на то, что storage является атрибутом класса
    # Объект self.storage для всех экземмпляров класса EchoServerClientProtocol
    # будет являться одним и тем же объектом для хранения метрик.
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
        except (UnicodeDecodeError, JSONDecodeError):
            return

        self._buffer = b''

        response = self.process(decoded_data, self.addr)

        # формируем успешный ответ
        self.transport.write(to_json(response))


def run_server(host, port):
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


if __name__ == "__main__":
    run_server('127.0.0.1', 8888)
