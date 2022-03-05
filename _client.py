import socket
import time
from threading import Thread
import os

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5002  # port we want to use

#Global variables
WINDOW_SIZE = 3
FRAME_SIZE = 50
TIMEOUT = 3

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket_tcp = self.socket_tcp_init()
        self.socket_udp = self.socket_udp_init()

    # initialize TCP socket
    def socket_tcp_init(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_ip, self.server_port))
        print('Connect to server')
        return s

    # initialize UDP socket
    def socket_udp_init(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return s

    #Listen to the client's requests
    def send_listen(self):
        def listen_for_messages():
            while True:
                message = self.socket_tcp.recv(1024).decode()
                print("\n" + message)
                

        # Download file
        def download(to_send):
            file_name = to_send.replace('<download>', '')
            self.socket_udp.sendto(to_send.encode(), (self.server_ip, self.server_port))
            msg, addr = self.socket_udp.recvfrom(FRAME_SIZE)
            file_size = int(msg.decode())
            bytes_recv = 0
            with open(file_name, "ab") as f:
                while bytes_recv <= file_size: #while we did not finish to add the content file to the buffer
                    buffer = [0] * WINDOW_SIZE #each time the window is emptied
                    try:
                        frame_recv = 0
                        for i in range(WINDOW_SIZE):
                            self.socket_udp.settimeout(TIMEOUT)
                            msg, addr = self.socket_udp.recvfrom(FRAME_SIZE)
                            frame_recv += 1
                            buffer_idx = int(chr(msg[0])) #number of packet
                            buffer[buffer_idx] = msg[1:] #Inserting the content into the buffer according to
                                                            # the serial number of the packets
                    except Exception as e:
                        if bytes_recv + (frame_recv * (FRAME_SIZE - 1)) >= file_size:
                            self.socket_udp.sendto('<ack>'.encode(), (self.server_ip, self.server_port))
                            bytes_recv += (FRAME_SIZE - 1) * frame_recv
                            for i in range(frame_recv):
                                f.write(buffer[i])
                        else:
                            continue
                    else:
                        self.socket_udp.sendto('<ack>'.encode(), (self.server_ip, self.server_port))
                        bytes_recv += (FRAME_SIZE - 1) * frame_recv
                        for i in range(frame_recv):
                            f.write(buffer[i])
                            # Once the buffer contains all the contents of the file,
                            # we will write it to the file

            print("you downloaded 100% out of file.")


        t = Thread(target=listen_for_messages)
        t.start()

        while True:
            #Wait for the request from the client and check what the request is
            # and according to that what the appropriate socket is
           user_input = input()
           if user_input.startswith('<download>'):
                download_thread  = Thread(target=download, args=(user_input,))
                download_thread.start()
           else:
                self.socket_tcp.send(user_input.encode())




        self.socket_tcp.close()




def main():
    client = Client(SERVER_IP, SERVER_PORT)
    client.send_listen()


if __name__ == '__main__':
    main()
