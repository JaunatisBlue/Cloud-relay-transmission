import os
import struct
import json
import time
from socket import *
import sys
import torch
import torch.nn as nn
import torch.utils.data as data
from torch.autograd import Variable as V
from threading import Thread
import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import pickle

from networks.unet import Unet
from networks.dunet import Dunet
from networks.dinknet import LinkNet34, DinkNet34, DinkNet50, DinkNet101, DinkNet34_less_pool
server = socket()
IP="127.0.0.1"
PORT=4027
server.bind((IP, PORT))
server.listen(10)

if len(sys.argv) > 1:
    index = sys.argv.index("-ip")
    IP = sys.argv[index + 1]

BATCHSIZE_PER_CARD = 4


class TTAFrame():
    def __init__(self, net):
        self.net = net().cuda()
        self.net = torch.nn.DataParallel(self.net, device_ids=range(torch.cuda.device_count()))

    def test_one_img_from_path(self, path, evalmode=True):
        if evalmode:
            self.net.eval()
        batchsize = 2
        if batchsize >= 8:
            return self.test_one_img_from_path_1(path)
        elif batchsize >= 4:
            return self.test_one_img_from_path_2(path)
        elif batchsize >= 2:
            return self.test_one_img_from_path_4(path)

    def test_one_img_from_path_8(self, path):
        img = cv2.imread(path)  # .transpose(2,0,1)[None]
        img90 = np.array(np.rot90(img))
        img1 = np.concatenate([img[None], img90[None]])
        img2 = np.array(img1)[:, ::-1]
        img3 = np.array(img1)[:, :, ::-1]
        img4 = np.array(img2)[:, :, ::-1]

        img1 = img1.transpose(0, 3, 1, 2)
        img2 = img2.transpose(0, 3, 1, 2)
        img3 = img3.transpose(0, 3, 1, 2)
        img4 = img4.transpose(0, 3, 1, 2)

        img1 = V(torch.Tensor(np.array(img1, np.float32) / 255.0 * 3.2 - 1.6).cuda())
        img2 = V(torch.Tensor(np.array(img2, np.float32) / 255.0 * 3.2 - 1.6).cuda())
        img3 = V(torch.Tensor(np.array(img3, np.float32) / 255.0 * 3.2 - 1.6).cuda())
        img4 = V(torch.Tensor(np.array(img4, np.float32) / 255.0 * 3.2 - 1.6).cuda())

        maska = self.net.forward(img1).squeeze().cpu().data.numpy()
        maskb = self.net.forward(img2).squeeze().cpu().data.numpy()
        maskc = self.net.forward(img3).squeeze().cpu().data.numpy()
        maskd = self.net.forward(img4).squeeze().cpu().data.numpy()

        mask1 = maska + maskb[:, ::-1] + maskc[:, :, ::-1] + maskd[:, ::-1, ::-1]
        mask2 = mask1[0] + np.rot90(mask1[1])[::-1, ::-1]

        return mask2

    def test_one_img_from_path_4(self, path):
        img = cv2.imread(path)  # .transpose(2,0,1)[None]
        img90 = np.array(np.rot90(img))
        img1 = np.concatenate([img[None], img90[None]])
        img2 = np.array(img1)[:, ::-1]
        img3 = np.array(img1)[:, :, ::-1]
        img4 = np.array(img2)[:, :, ::-1]

        img1 = img1.transpose(0, 3, 1, 2)
        img2 = img2.transpose(0, 3, 1, 2)
        img3 = img3.transpose(0, 3, 1, 2)
        img4 = img4.transpose(0, 3, 1, 2)

        img1 = V(torch.Tensor(np.array(img1, np.float32) / 255.0 * 3.2 - 1.6).cuda())
        img2 = V(torch.Tensor(np.array(img2, np.float32) / 255.0 * 3.2 - 1.6).cuda())
        img3 = V(torch.Tensor(np.array(img3, np.float32) / 255.0 * 3.2 - 1.6).cuda())
        img4 = V(torch.Tensor(np.array(img4, np.float32) / 255.0 * 3.2 - 1.6).cuda())

        maska = self.net.forward(img1).squeeze().cpu().data.numpy()
        maskb = self.net.forward(img2).squeeze().cpu().data.numpy()
        maskc = self.net.forward(img3).squeeze().cpu().data.numpy()
        maskd = self.net.forward(img4).squeeze().cpu().data.numpy()

        mask1 = maska + maskb[:, ::-1] + maskc[:, :, ::-1] + maskd[:, ::-1, ::-1]
        mask2 = mask1[0] + np.rot90(mask1[1])[::-1, ::-1]

        return mask2

    def test_one_img_from_path_2(self, path):
        img = cv2.imread(path)  # .transpose(2,0,1)[None]
        img90 = np.array(np.rot90(img))
        img1 = np.concatenate([img[None], img90[None]])
        img2 = np.array(img1)[:, ::-1]
        img3 = np.concatenate([img1, img2])
        img4 = np.array(img3)[:, :, ::-1]
        img5 = img3.transpose(0, 3, 1, 2)
        img5 = np.array(img5, np.float32) / 255.0 * 3.2 - 1.6
        img5 = V(torch.Tensor(img5).cuda())
        img6 = img4.transpose(0, 3, 1, 2)
        img6 = np.array(img6, np.float32) / 255.0 * 3.2 - 1.6
        img6 = V(torch.Tensor(img6).cuda())

        maska = self.net.forward(img5).squeeze().cpu().data.numpy()  # .squeeze(1)
        maskb = self.net.forward(img6).squeeze().cpu().data.numpy()

        mask1 = maska + maskb[:, :, ::-1]
        mask2 = mask1[:2] + mask1[2:, ::-1]
        mask3 = mask2[0] + np.rot90(mask2[1])[::-1, ::-1]

        return mask3

    def test_one_img_from_path_1(self, path):
        img = cv2.imread(path)  # .transpose(2,0,1)[None]

        img90 = np.array(np.rot90(img))
        img1 = np.concatenate([img[None], img90[None]])
        img2 = np.array(img1)[:, ::-1]
        img3 = np.concatenate([img1, img2])
        img4 = np.array(img3)[:, :, ::-1]
        img5 = np.concatenate([img3, img4]).transpose(0, 3, 1, 2)
        img5 = np.array(img5, np.float32) / 255.0 * 3.2 - 1.6
        img5 = V(torch.Tensor(img5).cuda())

        mask = self.net.forward(img5).squeeze().cpu().data.numpy()  # .squeeze(1)
        mask1 = mask[:4] + mask[4:, :, ::-1]
        mask2 = mask1[:2] + mask1[2:, ::-1]
        mask3 = mask2[0] + np.rot90(mask2[1])[::-1, ::-1]

        return mask3

    def load(self, path):
        self.net.load_state_dict(torch.load(path))

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
                time.sleep(0.3)
                num -= 1
        received_data += chunk

    return received_data
def daolu():
    source = 'received_images/'
    solver = TTAFrame(DinkNet34)
    solver.load('weights/log01_dink34.th')
    tic = time()
    target = 'submits/log01_dink34/'
    if not os.path.exists(target):
        os.mkdir(target)
    while True:
        val = os.listdir(source)
        for i, name in enumerate(val):
            print(name)
            if i % 10 == 0:
                print(i / 10, '    ', '%.2f' % (time() - tic))
            print("Attempting to load:", source + name)
            try:
                mask = solver.test_one_img_from_path(source + name)
                if mask is None:
                    print(f"Failed to load image {source + name}. Skipping...")
                    continue
                mask[mask > 4.0] = 255
                mask[mask <= 4.0] = 0
                mask = np.concatenate([mask[:, :, None], mask[:, :, None], mask[:, :, None]], axis=2)
                cv2.imwrite(target + name.split('.')[0] + 'mask.png', mask.astype(np.uint8))
                os.remove(source + name)  # 处理完成后删除源文件
            except Exception as e:
                print(f"Error processing image {source + name}: {e}")
        time.sleep(5)  # 等待1秒后重新检查文件夹




while True:
    save_folder = 'received_images2'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    conn, client_addr = server.accept()
    print(client_addr)

    print("socket2")
    client2 = socket()
    client2.connect((IP, 6000))
    client2.send("0".encode())
    #thread = Thread(target=daolu(), args=())
    #thread.start()
    while True:
        while True:
            # 接收文件名和文件大小信息
            filename_info = conn.recv(1024).decode('utf-8').strip()
            print(f"Received filename_info: {filename_info}")
            filename, filesize = filename_info.split('|')
            print(f"Received filename: {filename}")
            filename = os.path.basename(filename)
            filesize = int(filesize)
            # 接收文件数据
            received_data = b''
            while len(received_data) < filesize:
                packet = conn.recv(200000)
                if not packet:
                    break
                received_data += packet
            if received_data:
                with open('./'+save_folder+'/'+filename, 'wb') as f:
                    f.write(received_data)
                print(f"[+] 文件 '{filename}' 接收并保存成功")
    print("okokokok")
    break





















'''/////////////////////////////////////////////////////////////////////'''





import base64
import multiprocessing
import os
import struct
import socketserver
import json
import time
from filelock import FileLock
from socket import *
import logging
from conf import settings_c as settings
from lib import common
import cv2  # 需要安装 OpenCV 库
import numpy as np
from threading import Thread
# 配置日志系统，将 filelock 的日志级别设置为 ERROR
logging.getLogger("filelock").setLevel(logging.ERROR)


logger = common.load_my_logging_cfg('client')

dir_ = "."

ip_port = ('127.0.0.1', 6000)

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
    def image_slice(file_name):
        time.sleep(10)
        # 监视的文件夹路径
        folder_path = "cache" + "/" + file_name
        print(folder_path)
        # 输出合成图片的路径
        output_path = "db/C/" + file_name
        print(output_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        # 初始化图像列表
        images = []
        # 获取文件夹中已存在的图片
        existing_images = []
        # 开始监视文件夹变化并进行合成
        while True:
            # 获取当前文件夹中的所有文件
            current_files = os.listdir(folder_path)
            # 找出新增的图片文件
            new_images = [f for f in current_files if f.endswith('.png') and f not in existing_images]
            # 如果有新图片，则进行处理
            if new_images:
                for img_file in new_images:
                    # 加载图片
                    img_path = os.path.join(folder_path, img_file)
                    img = cv2.imread(img_path)

                    # 解析文件名，获取行列信息
                    parts = img_file.split('_')
                    if len(parts) != 2:
                        continue
                    try:
                        row = int(parts[0])
                        col = int(parts[1].split('.')[0])
                    except ValueError:
                        continue

                    # 根据行列信息动态扩展 images 列表
                    while row >= len(images):
                        images.append([])

                    images[row].append(img)

                    # 更新已存在图片列表
                    existing_images.append(img_file)

            # 检查是否有足够的图片进行合成
            if all(len(row_images) > 0 for row_images in images):
                # 确定行列数
                rows = len(images)
                cols = max(len(row_images) for row_images in images)

                # 创建新的合成图片
                composite_image = np.zeros((rows * images[0][0].shape[0], cols * images[0][0].shape[1], 3),
                                           dtype=np.uint8)

                for r in range(rows):
                    for c in range(len(images[r])):
                        composite_image[r * images[r][c].shape[0]:(r + 1) * images[r][c].shape[0],
                        c * images[r][c].shape[1]:(c + 1) * images[r][c].shape[1]] = images[r][c]

                # 保存合成图片
                output_file = os.path.join(output_path, f'result.png')
                cv2.imwrite(output_file, composite_image)

                # 清空 images 列表
                images = []
                existing_images = []





    def merge_slice(file_name, slice_num, dir_, curr_merge_slice_id=0, timeout=2, waiting_times=3):
        time.sleep(2)

        save_dir = dir_ + "/" + "cache" + "/" + file_name

        merge_file = dir_ + "/db/C/" + file_name

        if not os.path.isfile(merge_file):
            open(merge_file, 'a').close()

        # 2.5.2 合并后台收到的分片

        with open(merge_file, 'wb+') as merge_file_open:
        # merge_file_open = open(merge_file, "wb+")
        # merge_file_open.flush()
            waiting_times_ = 3
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
            file_size, titlehead = decode_file_head(file_head)
            save_file = dir_ + "/" + "cache" + "/" + titlehead
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
            received_data = []
            recv_size = 0

            # 实际分片片大小
            slice_size = 512000 + 170701

            # out_size = file_size + file_size * 170701 / 512000
            if k == 0:
                k = 1
                thread = Thread(target=DJLServer.image_slice, args=('result',))
                thread.start()
            while True:

                # time.sleep(0.8)
                # try:
                # 接收文件名和文件大小信息
                filename_info = conn.recv(1024).decode('utf-8').strip()
                filename, filesize = filename_info.split('|')
                filename = os.path.basename(filename)
                filesize = int(filesize)
                # 接收文件数据
                received_data = b''
                while len(received_data) < filesize:
                    packet = conn.recv(200000)
                    if not packet:
                        break
                    received_data += packet
                if received_data:
                    with open('./cache/' + 'result' + '/'+filename, 'wb') as f:
                        f.write(received_data)
                    print(f"[+] 文件 '{filename}' 接收并保存成功")
                # 异步线程池
                #pool.apply_async(save_slice, (filename, index, data, dir_,))
            # pool.close()
            # pool.join()




if __name__ == "__main__":
    pool = multiprocessing.Pool(processes=3)
    server = socketserver.ThreadingTCPServer(ip_port, DJLServer)
    # 激活服务端
    server.serve_forever()









