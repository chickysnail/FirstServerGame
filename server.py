import socket
from random import choice, randint
from time import sleep
from player import Player
from signal import SIGINT, signal
from sys import exit
from json import load
from threading import Event


class Server:
    def __init__(self, host: str, port: int) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        self.game_run = Event()
        self.game_run.set()

        signal(SIGINT, self.terminate)

    def terminate(self, *args) -> None:
        self.send_to_clients('Server closed the connection')
        self.send_to_clients('!CLOSE')
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()
        exit()

    def send_to_clients(self, message: str) -> None:
        for _, client_socket in self.client_sockets.items():
            client_socket.sendall(f'{message}\n'.encode())
        sleep(2)

    def set_order(self) -> None:
        choice(self.players).order = 1
        next(player for player in self.players if not player.order).order = 2

    def reset_players(self) -> None:
        for player in self.players:
            player.reset()

    @staticmethod
    def parse_message(message: bytes) -> str:
        return message.decode('utf-8').rstrip()

    def is_full(self):
        return True if len(self.client_sockets) == 2 else False

    def create_task(self):
        self.root1 = randint(-10,10)
        self.root2 = randint(-10,10)

        self.equation = f"x^2 "
        b = -(self.root1+self.root2)
        if b==1: self.equation += f"+ x "
        elif b==-1: self.equation += f"- x "
        elif b<0: self.equation += f"- {abs(b)}x "
        elif b>0: self.equation += f"+ {b}x "
        c = self.root1*self.root2
        if c<0: self.equation += f"- {abs(c)} "
        elif c>0: self.equation += f"+ {c} " 
        self.equation+="= 0"

    def calc_winner(self, first, second):
        winner = None
        if self.answers[first] in (self.root1, self.root2):
            if self.answers[second] in (self.root1, self.root2):
                result = 1
                if self.speeds[first]<self.speeds[second]: # decide winner by time
                    winner = first
                else: winner = second
            else: 
                result = 1 #one winner
                winner = first
        else:
            if self.answers[second] in (self.root1, self.root2):
                result = 1 
                winner = second
            else: 
                result = 0 #no winners
        return (result, winner)

    def run(self) -> None:
        self.client_sockets = {}
        self.answers = {}
        self.speeds = {}
        while True:
            if not self.is_full():
                client_socket, _ = self.server_socket.accept()
            client_socket.sendall(b'Choose username: ')
            sleep(1)
            client_socket.sendall(b'!USERNAME')
            username = client_socket.recv(1024)

            self.client_sockets[Player(username)] = client_socket
            if self.is_full():
                self.players = list(self.client_sockets.keys())
                # Game starts
                while self.game_run.is_set():
                    # phase 1
                    print("phase 1")
                    self.create_task()
                    self.send_to_clients(f'Players {" and ".join(map(str, self.client_sockets.keys()))} are ready!')
                    self.send_to_clients('Whose turn is first? Get ready...')
                    self.set_order()

                    # phase 2
                    print("phase 2")
                    players = list(self.client_sockets.keys())
                    first = next(player for player in players if player.order == 1)
                    second = next(player for player in players if player.order == 2)
                    self.send_to_clients(f'{first} is first!')
                    #first player
                    self.client_sockets[first].sendall(b"!INPUT!Press Enter when you are ready")
                    self.client_sockets[first].recv(1024)
                    self.client_sockets[first].sendall(f'!INPUT!Find one of the roots of this equation:\n{self.equation}'.encode())
                    pureresp = self.client_sockets[first].recv(1024).decode()
                    resp = pureresp.split("|")
                    self.answers[first] = int(resp[0])
                    self.speeds[first] = float(resp[1])
                    self.client_sockets[first].sendall(b"Answer recieved, other player's move")
                    #second player
                    self.client_sockets[second].sendall(f'{first} answered. Your turn!'.encode())
                    self.client_sockets[second].sendall(b"!INPUT!Press Enter when you are ready")
                    self.client_sockets[second].recv(1024)
                    self.client_sockets[second].sendall(f'!INPUT!Find one of the roots of this equation:\n{self.equation}'.encode())
                    pureresp = self.client_sockets[second].recv(1024).decode()
                    resp = pureresp.split("|")
                    self.answers[second] = int(resp[0])
                    self.speeds[second] = float(resp[1])
                    self.client_sockets[first].sendall(b"Answer recieved")
                    self.client_sockets[first].sendall(f'{second} answered'.encode())
                    self.send_to_clients('Calculating...')

                    # phase 3
                    print("phase 3")
                    res, winner = self.calc_winner(first, second)
                    if res == 0: mes = "You both lost"
                    elif res == 2: mes = "You both won!"
                    else: mes = f"{winner} won"
                    self.send_to_clients(mes)
                    
                    # retry ?
                    print("retry ?")
                    self.send_to_clients('One more round? (y/n)')
                    self.send_to_clients('!RETRY')
                    first_response = self.parse_message(self.client_sockets[first].recv(1024))
                    second_response = self.parse_message(self.client_sockets[second].recv(1024))
                    if first_response != 'y' or second_response != 'y':
                        self.game_run.clear()
                        self.terminate()
                        break
                    self.reset_players()
            else:
                self.send_to_clients('Waiting for other players...')


if __name__ == '__main__':
    with open('settings.json') as file:
        settings = load(file)
    Server(settings['HOST'], settings['PORT']).run()
