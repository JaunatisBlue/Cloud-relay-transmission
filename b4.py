import time
from socket import *
from threading import Thread
import os
import sys
import cv2

def carCheck(mp):
    print("车流检测")
    cap = cv2.VideoCapture(mp)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    file_name = os.path.basename(mp)
    output_file = os.path.join("result_mp4s", file_name)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))
    while cap.isOpened():
        ret, img = cap.read()
        if not ret:
            print("视频读取完毕")
            break
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        car_detector = cv2.CascadeClassifier("./cars.xml")
        cars = car_detector.detectMultiScale(gray, 1.2, 2, cv2.CASCADE_SCALE_IMAGE, (25, 25), (200, 200))
        for (x, y, w, h) in cars:
            print(x, y, w, h)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 1, cv2.LINE_AA)
        print("实时车流量", len(cars))
        text = "car number: " + str(len(cars))
        cv2.putText(img, text, (350, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 2)
        out.write(img)
        cv2.imshow("opencv", img)
        key = cv2.waitKey(10)
        if key == 27:
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()

server = socket()
IP="0.0.0.0"
PORT=4027
server.bind((IP, PORT))
server.listen(10)

if len(sys.argv) > 1:
    index = sys.argv.index("-ip")
    ip_s = sys.argv[index + 1]
    print(ip_s)

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


def daolu():
    time.sleep(3)
    no=0
    while True:
        val = os.listdir(source)
        for i, name in enumerate(val):
            print(name)
            if i % 10 == 0:
                print(i / 10)
            print("尝试加载:", source + name)
            carCheck(source + name)
            try:
                filesize2 = os.path.getsize(target+name.split(".")[0] + ".mp4")
                filename_info2 = f"{name.split('.')[0] + '.mp4'}|{filesize2}"
                print(f"发送: {filename_info2}")
                client2.send(filename_info2.encode("utf-8"))
                time.sleep(3)
                with open(target+name.split(".")[0] + ".mp4", "rb") as f:
                    content2 = f.read()
                    client2.sendall(content2)
                os.remove(source + name)
                os.remove(target + name)
                time.sleep(1)
            except Exception as e:
                print(f"Error processing image {source + name}: {e}")
        print("等待5s")
        no+=1
        time.sleep(5)
        if no>15:
            break


source = "received_images/"
target = "result_mp4s/"

while True:
    save_folder = "received_images"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    conn, client_addr = server.accept()
    print(client_addr)
    print("socket2")
    client2 = socket()
    client2.connect((ip_s, 6002))
    client2.send("0".encode())
    thread = Thread(target=daolu)
    thread.start()
    while True:
        while True:
            filename_info = conn.recv(1024).decode("utf-8").strip()
            print(f"收到文件: {filename_info}")
            filename, filesize = filename_info.split("|")
            filename = os.path.basename(filename)
            filesize = int(filesize)
            received_data = b""
            while len(received_data) < filesize:
                packet = conn.recv(200000)
                if not packet:
                    break
                received_data += packet
            if received_data:
                with open("./"+save_folder+"/"+filename, "wb") as f:
                    f.write(received_data)
    print("okokokok")
    break