import socket
from utils import *


class ClientError(Exception):
    """Общий класс исключений клиента"""
    pass


class ClientSocketError(ClientError):
    """Исключение, выбрасываемое клиентом при сетевой ошибке"""
    pass


class ClientProtocolError(ClientError):
    """Исключение, выбрасываемое клиентом при ошибке протокола"""
    pass


class Client:
    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        try:
            self.connection = socket.create_connection((host, port), timeout)
        except socket.error as err:
            raise ClientSocketError("error create connection", err)

    def _read(self):
        """Метод для чтения ответа сервера"""

        data = self.connection.recv(1024)

        # не забываем преобразовывать байты в объекты str для дальнейшей работы
        decoded_data = from_json(data)

        return decoded_data

    def put(self):

        # отправляем запрос команды put
        try:
            self.connection.sendall(to_json('ping'))
        except socket.error as err:
            raise ClientSocketError("error send data", err)

        # разбираем ответ
        print(self._read())

    def close(self):
        try:
            self.connection.close()
        except socket.error as err:
            raise ClientSocketError("error close connection", err)


if __name__ == "__main__":
    client = Client("192.168.100.185", 8888, timeout=5)
    client.put()

    client.close()
