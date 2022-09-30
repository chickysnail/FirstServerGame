import socket
from json import load
from time import time


class Client:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    @staticmethod
    def parse_message(message: bytes) -> str:
        return message.decode('utf-8').rstrip()

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            while True:
                data = s.recv(1024)
                message = self.parse_message(data)
                # print(f"LOG: {message}")
                if message.startswith('!'):
                    if message == '!CLOSE':
                        break
                    elif message.startswith('!INPUT!'):
                        temp1 = message.split("!INPUT!")
                        temp2 = temp1[1]
                        print(temp2)
                        t0 = time()
                        answer = input()
                        dt = time()-t0
                        s.sendall(f"{answer}|{dt}".encode())
                    else:
                        s.sendall((input()+" ").encode())
                else:
                    print(message)


if __name__ == '__main__':
    with open('settings.json') as file:
        settings = load(file)
    Client(settings['HOST'], settings['PORT']).run()
