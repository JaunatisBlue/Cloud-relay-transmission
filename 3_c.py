import base64
import multiprocessing
import os
import struct
import socketserver
import time
from filelock import FileLock
import logging
from lib import common
# 配置日志系统，将 filelock 的日志级别设置为 ERROR
logging.getLogger("filelock").setLevel(logging.ERROR)


logger = common.load_my_logging_cfg('client')

dir_ = "."

ip_port = ('0.0.0.0', 6000)

numss=0
now_slices=0
k=0
is_first=0
# 临时保存文件内容
def save_slice(file_name, slice_id, slice_content, dir_):
    # 保存文件分片
    slice_save_file = dir_ + "/" + "cache" + "/" + file_name + "/" + slice_id
    slice_save_file_lock = dir_ + "/" + "cache" + "/" + file_name + "/" + slice_id + '.lock'
    folder_name = dir_ + "/" + "cache" + "/" + file_name
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # 创建文件锁
    lock = FileLock(slice_save_file_lock)

    with lock:
        with open(slice_save_file, "wb") as f:
            f.write(base64.b64decode(slice_content))
    lock.release()

def receive_fixed_length_data(socket, length):
    received_data = b''  # 初始化接收的数据为空字节串

    while len(received_data) < length:
        remaining_length = length - len(received_data)  # 计算剩余需要接收的数据长度
        if(received_data[-2:]!=b'"}'):
            chunk = socket.recv(remaining_length)  # 接收数据
            if(chunk==b''):
                return received_data
        else:
            return received_data
        received_data += chunk  # 拼接接收到的数据

    return received_data


def decode_file_head(file_head):
    # 从文件头中解析文件大小和文件名
    file_size = struct.unpack('q', file_head[:8])[0]  # 解析前8个字节为文件大小
    # 解析文件名（去除补齐的空字节）
    filename_bytes = file_head[8:16]  # 剩余部分为文件名字节流
    filename = filename_bytes.rstrip(b'\x00').decode('ascii')  # 去除补齐的空字节，并解码为字符串

    return file_size, filename

class DJLServer(socketserver.BaseRequestHandler):
    def format_to_three_digits(number):
        return '{:08d}'.format(number)

    def time_trans(file_name, slice_num, dir_, curr_merge_slice_id=0, timeout=0.5):
        save_dir = dir_ + "/" + "cache" + "/" + file_name
        merge_file = dir_ + "/db/C/" + file_name
        if not os.path.isfile(merge_file):
            open(merge_file, 'a').close()

        time1 = time.time()

        waiting_times_ = 3
        # # 对于待每一个所要合并的分片最多循环等三次，防止所要合并分片还在传送的路上或还没写入磁盘
        while waiting_times_ and curr_merge_slice_id < slice_num:
            curr_merge_slice_file = save_dir + "/" + DJLServer.format_to_three_digits(curr_merge_slice_id)
            if DJLServer.format_to_three_digits(curr_merge_slice_id) in os.listdir(save_dir):
                curr_merge_slice_id += 1
                waiting_times_ = 3
            else:
                waiting_times_ -= 1
                time.sleep(timeout)

        time2 = time.time()
        print("传输完成，用时", time2 - time1, "s")

        return None

    def merge_slice(file_name, slice_num, dir_, curr_merge_slice_id=0, timeout=4, waiting_times=3):
        time.sleep(3)

        save_dir = dir_ + "/" + "cache" + "/" + file_name

        merge_file = dir_ + "/db/C/" + file_name

        if not os.path.isfile(merge_file):
            open(merge_file, 'a').close()

        # 2.5.2 合并后台收到的分片

        with open(merge_file, 'wb+') as merge_file_open:
        # merge_file_open = open(merge_file, "wb+")
        # merge_file_open.flush()
            waiting_times_ = 10
            # # 对于待每一个所要合并的分片最多循环等三次，防止所要合并分片还在传送的路上或还没写入磁盘
            while waiting_times_ and curr_merge_slice_id < slice_num:
                curr_merge_slice_file = save_dir + "/" + DJLServer.format_to_three_digits(curr_merge_slice_id)
                slice_save_file_lock = save_dir + "/" + DJLServer.format_to_three_digits(curr_merge_slice_id) + ".lock"
                if DJLServer.format_to_three_digits(curr_merge_slice_id) in os.listdir(save_dir):
                    # 创建文件锁
                    lock = FileLock(slice_save_file_lock)

                    with lock.acquire(timeout=3):
                        with open(curr_merge_slice_file, r"rb") as f:
                            curr_merge_slice_content = f.read()
                            f.flush()
                            print("curr_merge_slice_content len :",len(curr_merge_slice_content))
                    lock.release()

                    merge_file_open.write(curr_merge_slice_content)

                    merge_file_open.flush()  # 刷新缓冲区
                    print("已经合并的分片id：",curr_merge_slice_id)

                    curr_merge_slice_id += 1
                    waiting_times_ = 3
                else:
                    waiting_times_ -= 1
                    time.sleep(timeout)

        print("合并服务结束")
        return None


    def handle(self):
        global now_slices
        global numss
        global k
        global is_first
        global slice_num
        conn = self.request
        addr = self.client_address
        print(conn, addr)
        funct=conn.recv(1).decode()



        if funct=='1':
            print("进入断点判断...")
            k=0
            file_head = conn.recv(16)
            print("收到文件头...")
            file_size, filename = decode_file_head(file_head)
            print(filename+":"+str(file_size))
            save_file = dir_ + "/" + "cache" + "/" + filename
            if not os.path.exists(save_file):
                os.makedirs(save_file)
                conn.send("00000000".encode())
                print("发送断点...")
            curr_id = 0
            while True:
                if DJLServer.format_to_three_digits(curr_id) in os.listdir(save_file):
                    curr_id+=1
                    print(curr_id)
                else:
                    conn.send(DJLServer.format_to_three_digits(curr_id).encode())
                    print("发送断点...")
                    break

        if funct == '0':
            numss+=1
            #time.sleep(0.8)
            file_head = 0
            recv_size = 0
            conn = self.request
            addr = self.client_address
            print(conn, addr)

            file_head = conn.recv(16)

            print(file_head)
            file_size, filename = decode_file_head(file_head)
            print(file_size)
            print(filename)



            received_data = []
            recv_size = 0

            # 实际分片片大小
            slice_size = 512000 + 170701

            # out_size = file_size + file_size * 170701 / 512000

            while True:

                # time.sleep(0.8)
                # try:
                recv_data = receive_fixed_length_data(conn,slice_size)
                if (recv_data == b''):
                    # time2 = time.time()
                    # print("传输完成，用时", time2 - time1, "s")
                    #time.sleep(0.1)
                    break
                recv_dec = recv_data.decode("ascii")
                recv_dict = eval(recv_dec)

                data = None
                index = recv_dict["index"]
                data = recv_dict["data"]
                print(index)
                #print(data)

                # 异步线程池
                pool.apply_async(save_slice, (filename, index, data, dir_,))

                now_slices += 1

                recv_size += slice_size
                if k == 0:
                    k = 1
                    slice_num = int(file_size * numss / 512000) + 1
                    print(numss)
                    merge_slice = multiprocessing.Process(target=DJLServer.merge_slice,
                                                          args=(filename, slice_num, dir_))
                    print(slice_num)
                    merge_slice.start()
                    time_trans = multiprocessing.Process(target=DJLServer.time_trans,
                                                          args=(filename, slice_num, dir_))
                    time_trans.start()
                # if(recv_size>=out_size):
                #     break
                if(int(index)>=slice_num-1):
                    # time2 = time.time()
                    numss=0
                    # print("传输完成，用时", time2 - time1, "s")
            now_slices-=1
            # pool.close()
            # pool.join()




if __name__ == "__main__":
    pool = multiprocessing.Pool(processes=3)
    server = socketserver.ThreadingTCPServer(ip_port, DJLServer)
    # 激活服务端
    server.serve_forever()


