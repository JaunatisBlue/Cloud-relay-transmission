import base64
import os
import struct
import sys
import threading
from socket import *
import json
from lib import common
from conf import settings_a as settings
from threading import Thread
import time
import queue

logger = common.load_my_logging_cfg('server')

clients = []  # 存客户端数组
threads = []  # 线程数组
client0 = socket()
client0.connect(("35.76.1.177", 6000))
slicesize=0
allsize=0
ns=0
mark=0
lock = threading.RLock()
filename = "A.zip"
if len(sys.argv) > 1:
    # index = sys.argv.index('-f')
    # filename = sys.argv[index+1]
    filename = "A.zip"
    index = sys.argv.index('-n')
    nums = int(sys.argv[index+1])
    index = sys.argv.index('-ip')

def get_filename_list():
    """获取db/server下的所有文件名"""
    filename_list = os.listdir(settings.SERVER_DB_PATH)
    return filename_list


def get_file_content(filename, file_size):
    """通过文件名获取文件路径"""
    filename_path = os.path.join(settings.SERVER_DB_PATH, filename)
    with open(filename_path, 'rb') as fr:
        fr.seek(file_size, 0)
        file_content = fr.read(1024)

    return file_content


def send_file_content(ns,cl,n,filename, file_size, chunk_size=1024000):
    """通过文件名获取文件路径，并按块大小分片传输文件"""
    global mark
    filename_path = os.path.join(settings.SERVER_DB_PATH, filename)
    #print(n)
    #print(slicesize)
    end=int(filesize/512000)+1
    sendsize=0
    a=0
    while True:
        #print(n)
        if mark>=end:
            break
        # time.sleep(0.8)
        lock.acquire()
        while(True):
            if(mark<len(q)):
                file_content = q[mark]
                # 新添加的，没有运行验证
                q[mark] = None
                break
            else:
                time.sleep(1)
        num_str = str(mark).zfill(8)
        print("文件分片编号：",mark)
        mark += 1
        lock.release()
        base64_string = base64.b64encode(file_content).decode('utf-8')
        data_block = {"index":num_str,"data":str(base64_string)}
        # 将数据块转换为JSON并计算大小
        file_json = json.dumps(data_block)
        data_block_size = len(file_json.encode('utf-8'))
        print("数据块大小为:", data_block_size, "字节")
        #print(file_json)
        # print(file_json.encode("ascii"))
        #time.sleep(0.1)
        cl.send(file_json.encode("ascii"))
    timeb = time.time()
    t = timeb - timea
    print("t:" + str(t))



def set_file_head(filename, file_size):
    """设计一个文件头"""
    # 获取文件路径
    filename_path = os.path.join(settings.SERVER_DB_PATH, filename)
    global slicesize
    global allsize
    global ns
    global filesize
    filesize = os.path.getsize(filename_path) - file_size
    #print(file_size)
    slicesize = filesize/nums
    allsize = filesize
    slicesize = int(slicesize)
    nss = slicesize / 512000
    nss = int(nss) + 1
    ns = nss*nums
    num_str = str(ns)
    ns = len(num_str)
    # 获取文件大小和文件名字节流
    file_size_bytes = struct.pack('q', slicesize)  # 使用 'q' 格式表示长整型
    filename_bytes = filename.encode('ascii')

    # 补齐文件名至8个字节
    if len(filename_bytes) < 8:
        filename_bytes += b'\x00' * (8 - len(filename_bytes))

    # 构建文件头
    file_head = file_size_bytes + filename_bytes

    return file_head

def connect_with_retry(ID, PORT, client,max_retries=50, delay=5):
    attempt = 0
    while attempt < max_retries:
        try:
            client.connect((ID, PORT))
            return client
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            attempt += 1
            if attempt < max_retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Connection failed.")
    return None

print('start...')

# filename=input()
file_size=0
# nums=int(input("请输入要连接的客户端数："))
# 发送文件
file_head = set_file_head(filename, file_size)
# 发送文件头
while True:
    print(f"准备连接socket2")
    client0.send("1".encode())
    print(file_head)
    client0.send(file_head)
    print("发送文件头")
    recv=client0.recv(8)
    break
# print(f"{file_head}")
recv_id=recv.decode()
mark=int(recv_id)
print("mark:"+recv_id)
#nums=int(input("请输入要连接的客户端数："))
for i in range(1,nums+1):
    client = socket()
    ID= sys.argv[index + i]
    print(ID)
    PORT=4026
    connect_with_retry(ID, PORT,client)
    if client:
        clients.append(client)

"""client = socket()
client.connect(("127.0.0.1", 8000))
clients.append(client)
client2 = socket()
client2.connect(("127.0.0.1", 8001))
clients.append(client2)"""
for i in range(nums):
    clients[i].send(file_head)
q=[]
def read_file_into_queue(filename, q):
    smallslice = 512000
    max_size = 1000000000  # 设置队列最大大小（1GB）
    filename_path = os.path.join(settings.SERVER_DB_PATH, filename)
    with open(filename_path, 'rb') as fr:
        file_size = 0
        while True:
            if sys.getsizeof(q) >= max_size:
                print(f"队列已满，等待中... (当前大小：{q.qsize()})")
                time.sleep(2)  # 等待 5 秒钟
            else:
                file_content = fr.read(smallslice)
                if not file_content:  # 到达文件末尾
                    break
                q.append(file_content)
                file_size += len(file_content)
        print(f"文件读取完毕，共读取 {file_size} 字节。")

# 创建线程并启动
thread = threading.Thread(target=read_file_into_queue, args=(filename, q))
thread.start()
timea=time.time()
# 发送文件内容
for i in range(nums):
    thread = Thread(target=send_file_content, args=(ns,clients[i],i,filename, file_size))
    threads.append(thread)
    thread.start()
#send_file_content(filename, file_size)
logger.info(f'成功给{8000}发送文件{filename}')

# except ConnectionResetError:
    # break
    # client.close()
