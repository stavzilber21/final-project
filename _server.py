import socket
import os
from threading import Thread

SERVER_IP = "0.0.0.0"
SERVER_PORT = 5002  # port we want to use

#Global variables
WINDOW_SIZE = 3
FRAME_SIZE = 50
TIMEOUT = 3

class Server:
    def __init__(self, ip, port):
        self.clients = {}  # key:(client_socket, client_address), value: name
        self.ip = ip
        self.port = port
        self.socket_tcp = self.socket_tcp_init()
        self.socket_udp = self.socket_udp_init()

    # initialize TCP socket
    def socket_tcp_init(self):
        s = socket.socket()
        s.bind((self.ip, self.port))
        return s

    # initialize UDP socket
    def socket_udp_init(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.ip, self.port))
        return s

    #Handling each client who connects and using threades (processes) so that several clients can connect in parallel.
    def serve(self):
        print('Starting server')
        self.socket_tcp.listen(10)
        while True:
            client_socket, client_address = self.socket_tcp.accept()
            print('Connect to client')
            key = (client_socket, client_address)
            th_tcp = Thread(target=self.listen_for_client_tcp, args=(key,))
            th_udp = Thread(target=self.listen_for_client_udp)
            th_tcp.start()
            th_udp.start()

    #Handling a file download request by UDP
    def listen_for_client_udp(self):
        while True:
            try:
                # msg: client's message bytes
                # addr: client's (ip, port) tuple
                msg, addr = self.socket_udp.recvfrom(1024)  # buffer size is 1024 bytes
                msg = msg.decode()
            except Exception as e:
                print(f"[!] Error: {e}")
            else:
                if msg.startswith('<download>'):
                    self.download(msg, addr)

    #Handling client requests in part a
    def listen_for_client_tcp(self, key):
        while True:
            try:
                msg = key[0].recv(1024).decode()
            except Exception as e:
                print(f"[!] Error: {e}")
                del self.clients[key]


            else: #According to the beginning of the message, we will understand what
                # the client's request is and we will go to the appropriate function
                if msg.startswith('<connect>'):
                    self.connect_client(key, msg)
                if msg.startswith('<get_users>'):
                    self.get_users(key)
                if msg.startswith('<disconnect>'):
                    self.disconnect(key)
                if msg.startswith('<set_msg>'):
                    self.set_msg(msg, key)
                if msg.startswith('<set_msg_all>'):
                    self.set_msg_all(msg)
                if msg.startswith('<get_list_file>'):
                    self.get_list_file(key)

    #connect client to server and sending a message to all participants who connected
    def connect_client(self, key, msg):
        name = msg.replace('<connect>', '')
        self.clients[key] = name  # add the new client to the list
        print(f"{name} is connected")
        msg = f"<set_msg_all>{name} is connected"
        self.set_msg_all(msg)

    #View the list of users
    def get_users(self, key):
        list_users = ','.join(self.clients.values())
        key[0].send(list_users.encode())

    #Disconnect client from server and sending a message to all participants who disconnected
    def disconnect(self, key):
        name = self.clients[key]
        del self.clients[key]
        msg = f"<set_msg_all>{name} is disconnected"
        self.set_msg_all(msg)


    #Send a message to someone specific
    def set_msg(self, msg, keys):
        name_msg = msg.replace('<set_msg>', '')
        name = self.clients[keys]
        _name, msg = name_msg.split(' ', 1)
        msg = name + ": " + msg
        for key, user in self.clients.items():
            if user == _name:
                key[0].send(msg.encode())

    #Send a message to all chat participants
    def set_msg_all(self, msg):
        msg = msg.replace('<set_msg_all>', '')
        for key in self.clients.keys():
            key[0].send(msg.encode())

    #View the list of files
    def get_list_file(self, key):
        files = []
        for x in os.listdir():
            if os.path.isfile(x):
                files.append(x)
        list_files = ','.join(files)
        key[0].send(list_files.encode())

    #Download file
    def download(self, msg, addr):
        file_name = msg.replace('<download>', '')
        with open(file_name, "rb") as f:  # return the contect in bytes
            file_data = f.read()
        file_size = len(file_data)
        self.socket_udp.sendto(str(len(file_data)).encode(), addr)  # send the size of the file
        bytes_sent = 0
        while bytes_sent <= file_size: #while we did not finish transferring the entire file
            try:
                curr_bytes_sent = bytes_sent
                for i in range(WINDOW_SIZE):
                    if curr_bytes_sent >= file_size:
                        break
                    self.socket_udp.sendto(
                        str(i).encode() + file_data[curr_bytes_sent:curr_bytes_sent + FRAME_SIZE - 1], addr)
                    curr_bytes_sent += FRAME_SIZE - 1
                    #str(i) is the serial number of the FRAME in order for them to arrive in order
                self.socket_udp.settimeout(TIMEOUT * 2)
                msg, addr = self.socket_udp.recvfrom(FRAME_SIZE)
            except Exception as e:
                continue
            else:
                self.socket_udp.settimeout(None)
                bytes_sent += (FRAME_SIZE - 1) * WINDOW_SIZE #add all the extra bytes we have already sent


def main():
    server = Server(SERVER_IP, SERVER_PORT)
    server.serve()


if __name__ == '__main__':
    main()
