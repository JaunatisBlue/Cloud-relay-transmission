# -*- coding: utf-8 -*-
import struct
import time
from socket import *
import sys

server = socket()
IP="0.0.0.0"
PORT=4026
server.bind((IP, PORT))
server.listen(10)

if len(sys.argv) > 1:
    index = sys.argv.index("-ip")
    IP = sys.argv[index + 1]

def receive_fixed_length_data(socket, length):
    received_data = b""
    num = 3
    while len(received_data) < length:
        remaining_length = length - len(received_data)
        chunk = socket.recv(remaining_length)
        if not chunk:
            if num == 0:
                return received_data
            else:
                time.sleep(1)
                num -= 1
        received_data += chunk

    return received_data

while True:
    conn, client_addr = server.accept()
    print(client_addr)

    print("socket2")
    client2 = socket()
    client2.connect((IP, 6000))
    client2.send("0".encode())

    file_head = conn.recv(16)
    client2.send(file_head)
    file_size = struct.unpack("q", file_head[:8])[0]  # file_size

    out_size = file_size + file_size * 170701 / 512000

    print(f"大小: {file_size}")
    recv_size = 0
    is_first = 1

    slice_size = 512000 + 170701

    while True:
        #time.sleep(0.1)
        file_content = receive_fixed_length_data(conn, slice_size)
        if file_content == b"":
            break
        recv_dec = file_content.decode("ascii")
        #recv_dict = eval(recv_dec)
        # recv_size += slice_size
        data = None
        #index = recv_dict["index"]
        #print(index)
        client2.send(file_content)

    print("okokokok")
    break