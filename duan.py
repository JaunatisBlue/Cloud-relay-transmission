import os
import struct
import json
import time
import sys
from socket import *
server = socket()
server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
IP="127.0.0.1"
PORT=5026
server.bind((IP, PORT))
server.listen(5)
if len(sys.argv) > 1:
    index = sys.argv.index('-ip')
    IP = sys.argv[index + 1]

while True:
    conn, client_addr = server.accept()
    print(client_addr)
    print(IP)
    print(f"准备连接socket2")
    client2 = socket()
    client2.connect((IP, 6000))
    client2.send("1".encode())

    # 发送文件头
    #print("准备发送文件头")
    file_head = conn.recv(16)
    print("收到文件头")
    print(file_head)
    client2.send(file_head)
    print("发送文件头")
    recv_id=client2.recv(8)
    print("收到id")
    conn.send(recv_id)
    print("发送id")
    break




