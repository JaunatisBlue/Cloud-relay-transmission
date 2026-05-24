import time
from socket import *
from threading import Thread
import os
import sys
import cv2

def carCheck(mp):
    print("车流检测")
    # 读取加载视频
    cap = cv2.VideoCapture(mp)

    # 获取视频的宽度和高度
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)  # 获取视频的帧率

    # 定义编解码器并创建VideoWriter对象
    # 使用 os.path.basename() 提取文件名
    file_name = os.path.basename(mp)
    output_file = os.path.join('result_mp4s', file_name)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用 'mp4v' 编解码器
    out = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

    # 读取一帧图片
    while cap.isOpened():  # 检查视频是否打开
        ret, img = cap.read()
        if not ret:  # 如果读取帧失败，说明视频读取完毕
            print("视频读取完毕")
            break

        # 灰度
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        # 加载级联分类器
        car_detector = cv2.CascadeClassifier("./cars.xml")

        cars = car_detector.detectMultiScale(gray, 1.2, 2, cv2.CASCADE_SCALE_IMAGE, (25, 25), (200, 200))
        # 画框框
        for (x, y, w, h) in cars:
            print(x, y, w, h)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 1, cv2.LINE_AA)

        print("实时车流量", len(cars))
        text = 'car number: ' + str(len(cars))
        # 添加文字
        cv2.putText(img, text, (350, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 2)

        # 写入帧
        out.write(img)

        cv2.imshow("opencv", img)
        key = cv2.waitKey(10)  # 延时并且监听按键
        if key == 27:  # 按ESC键退出
            break

    # 释放资源
    cap.release()
    out.release()
    cv2.destroyAllWindows()  # 关闭所有窗口



###############绑定自己的ip
server = socket()
IP="0.0.0.0"
PORT=4027
server.bind((IP, PORT))
server.listen(10)

if len(sys.argv) > 1:
    index = sys.argv.index("-ip")
    IP = sys.argv[index + 1]

BATCHSIZE_PER_CARD = 4

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


def daolu():####################要使用的模型
    time.sleep(3)
    while True:
        val = os.listdir(source)
        for i, name in enumerate(val):
            print(name)
            if i % 10 == 0:
                print(i / 10)
            print("尝试加载:", source + name)
            carCheck(source + name)
            try:
                # 发送文件名和文件大小信息
                filesize2 = os.path.getsize(target+name.split('.')[0] + '.mp4')
                filename_info2 = f"{name.split('.')[0] + '.mp4'}|{filesize2}"
                print(f"发送: {filename_info2}")
                client2.send(filename_info2.encode('utf-8'))
                time.sleep(1)
                # 发送文件内容（示例中省略）
                with open(target+name.split('.')[0] + '.mp4', 'rb') as f:
                    content2 = f.read()
                    client2.sendall(content2)
                os.remove(source + name)  # 处理完成后删除源文件
                os.remove(target + name)  # 处理完成后删除源文件
                time.sleep(1)
            except Exception as e:
                print(f"Error processing image {source + name}: {e}")
        print("等待5s")
        time.sleep(5)  # 等待5秒后重新检查文件夹


source = 'received_images/'
target = 'result_mp4s/'

while True:
    save_folder = 'received_images'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    conn, client_addr = server.accept()###################被a连接
    print(client_addr)
    print("socket2")
    client2 = socket()
    client2.connect(("47.129.29.44", 6000))##############连接c
    client2.send("0".encode())
    thread = Thread(target=daolu)
    thread.start()
    while True:
        while True:
            # 接收文件名和文件大小信息
            filename_info = conn.recv(1024).decode('utf-8').strip()
            print(f"收到文件: {filename_info}")
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
                with open('./'+save_folder+'/'+filename, 'wb') as f:
                    f.write(received_data)

    print("okokokok")
    break