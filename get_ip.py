import os
import time
import re

# 目标日志文件路径
log_file_path = r"C:\Users\22748\Desktop\chuanshu\cloudsstorm\Logs\InfrasCode.log"

# 正则表达式用于提取 pubIP 后面的 IP 地址
pubip_pattern = re.compile(r'pubIP:\s*"([\d\.]+)"')

# 存储提取的 IP 地址
ip_list = []
with open("output.txt", "w") as file:
    # 写入数组中的每个元素
    file.write("1")
# 等待日志文件生成并且只有一行
while True:
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as log_file:
            lines = log_file.readlines()
            if len(lines) > 3:
                break
    time.sleep(1)  # 每秒检查一次

print(f"Log file {log_file_path} found and it is not empty. Reading contents...")

# 读取文件内容并提取 IP 地址
with open(log_file_path, 'r', encoding='utf-8') as file:
    content = file.read()
    ip_list = pubip_pattern.findall(content)

print("Extracted IP addresses:", ip_list)
# 打开 txt 文件进行写操作

with open("output.txt", "w") as file:
    # 写入数组中的每个元素
    file.write("2")
with open("output.txt", "w") as file:
    # 写入数组中的每个元素
    for item in ip_list:
        file.write(f"{item}\n")
