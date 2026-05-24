import os
import subprocess
import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QPushButton, QMessageBox, QLineEdit, QDialog,
                             QGroupBox, QFileDialog)
import example
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("基于云中转的多路传输技术")
        self.setFixedSize(500, 250)  # 增大主窗口尺寸

        # 可用地区选项
        self.regions = ["加利福尼亚", "圣保罗", "伦敦", "新加坡", "悉尼", "首尔",
                        "孟买", "法兰克福", "弗吉尼亚", "俄勒冈", "东京", "中部"]

        self.initUI()

    def initUI(self):
        # 主窗口部件
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # 起始地址选择
        start_layout = QHBoxLayout()
        start_label = QLabel("起始地址:")
        self.start_combo = QComboBox()
        self.start_combo.addItems(self.regions)
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_combo)

        # 终点地址选择
        end_layout = QHBoxLayout()
        end_label = QLabel("终点地址:")
        self.end_combo = QComboBox()
        self.end_combo.addItems(self.regions)
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_combo)

        # 确定按钮
        confirm_btn = QPushButton("确定")
        confirm_btn.setFixedHeight(40)  # 增大按钮高度
        confirm_btn.clicked.connect(self.on_confirm)

        # 添加到主布局
        main_layout.addLayout(start_layout)
        main_layout.addLayout(end_layout)
        main_layout.addWidget(confirm_btn)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def on_confirm(self):
        start_region = self.start_combo.currentText()
        end_region = self.end_combo.currentText()

        if start_region == end_region:
            QMessageBox.warning(self, "错误", "起始地址和终点地址不能相同！")
            return

        try:
            # 调用road函数并获取结果
            result1, time1, cost1, result2, time2, cost2, result3, time3, cost3 = example.road(start_region, end_region)
            result1=result1[0:2]
            result2 = result2[0:2]
            result3 = result3[0:2]
            # 格式化路径为"地区1 地区2"的形式
            formatted_result1 = self.format_path(result1)
            formatted_result2 = self.format_path(result2)
            formatted_result3 = self.format_path(result3)

            # 保存原始结果路径用于写入文件
            self.result_paths = {
                1: formatted_result1,
                2: formatted_result2,
                3: formatted_result3
            }

            # 格式化时间和成本为三位小数
            results = [
                formatted_result1, f"{float(time1):.3f}", f"{float(cost1):.3f}",
                formatted_result2, f"{float(time2):.3f}", f"{float(cost2):.3f}",
                formatted_result3, f"{float(time3):.3f}", f"{float(cost3):.3f}"
            ]

            self.show_solution_dialog(start_region, end_region, results)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行出错: {str(e)}")

    def format_path(self, path):
        """将路径格式化为'地区1 地区2'的形式"""
        if isinstance(path, list):
            return " ".join(path)
        elif isinstance(path, str) and path.startswith("[") and path.endswith("]"):
            # 处理字符串形式的列表
            path = path[1:-1].replace("'", "").replace(",", "")
            return path
        return path

    def show_solution_dialog(self, start_region, end_region, results):
        dialog = QDialog(self)
        dialog.setWindowTitle("选择传输方案")
        dialog.setFixedSize(900, 500)  # 增大对话框尺寸

        layout = QVBoxLayout()

        # 方案选择标题
        title_label = QLabel("请选择传输方案:")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        # 文件选择按钮
        file_btn = QPushButton("选择传输文件")
        file_btn.clicked.connect(self.select_file)
        layout.addWidget(file_btn)

        # 显示选择的文件路径
        self.file_label = QLabel("未选择文件")
        layout.addWidget(self.file_label)

        # 三种方案横向排列
        solutions_layout = QHBoxLayout()
        print(results)
        # 方案1
        sol1_group = QGroupBox("方案1")
        sol1_layout = QVBoxLayout()
        sol1_result = QLabel(f"<b>路径:</b> {results[0]}")
        sol1_time = QLabel(f"<b>速率:</b> {results[1]}KB/s")
        sol1_cost = QLabel(f"<b>成本:</b> {results[2]} 美元")
        sol1_btn = QPushButton("选择此方案")
        sol1_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        sol1_btn.clicked.connect(lambda: self.on_solution_selected(1, dialog))

        sol1_layout.addWidget(sol1_result)
        sol1_layout.addWidget(sol1_time)
        sol1_layout.addWidget(sol1_cost)
        sol1_layout.addWidget(sol1_btn)
        sol1_group.setLayout(sol1_layout)

        # 方案2
        sol2_group = QGroupBox("方案2")
        sol2_layout = QVBoxLayout()
        sol2_result = QLabel(f"<b>路径:</b> {results[3]}")
        sol2_time = QLabel(f"<b>时间:</b> {results[4]} 毫秒")
        sol2_cost = QLabel(f"<b>成本:</b> {results[5]} 美元")
        sol2_btn = QPushButton("选择此方案")
        sol2_btn.setStyleSheet("background-color: #2196F3; color: white;")
        sol2_btn.clicked.connect(lambda: self.on_solution_selected(2, dialog))

        sol2_layout.addWidget(sol2_result)
        sol2_layout.addWidget(sol2_time)
        sol2_layout.addWidget(sol2_cost)
        sol2_layout.addWidget(sol2_btn)
        sol2_group.setLayout(sol2_layout)

        # 方案3
        sol3_group = QGroupBox("方案3")
        sol3_layout = QVBoxLayout()
        sol3_result = QLabel(f"<b>路径:</b> {results[6]}")
        sol3_time = QLabel(f"<b>时间:</b> {results[7]} 毫秒")
        sol3_cost = QLabel(f"<b>成本:</b> {results[8]} 美元")
        sol3_btn = QPushButton("选择此方案")
        sol3_btn.setStyleSheet("background-color: #FF9800; color: white;")
        sol3_btn.clicked.connect(lambda: self.on_solution_selected(3, dialog))

        sol3_layout.addWidget(sol3_result)
        sol3_layout.addWidget(sol3_time)
        sol3_layout.addWidget(sol3_cost)
        sol3_layout.addWidget(sol3_btn)
        sol3_group.setLayout(sol3_layout)

        # 添加到方案布局
        solutions_layout.addWidget(sol1_group)
        solutions_layout.addWidget(sol3_group)

        # IP地址输入
        ip_group = QGroupBox("终点服务器设置")
        ip_layout = QHBoxLayout()
        ip_label = QLabel("服务器IP:")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("接收端IP")
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        ip_group.setLayout(ip_layout)

        # 添加到主布局
        layout.addLayout(solutions_layout)
        layout.addWidget(ip_group)
        dialog.setLayout(layout)

        self.selected_solution = None
        self.selected_file = None  # 用于存储选择的文件路径
        dialog.exec_()

    def select_file(self):
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(self, "选择传输文件", "db/A", "All Files (*)")
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(f"已选择文件: {file_path}")

    def on_solution_selected(self, solution_num, dialog):
        ip_address = self.ip_input.text().strip()

        if not ip_address:
            QMessageBox.warning(dialog, "错误", "请输入终点服务器IP地址！")
            return

        # IP地址简单验证
        if not self.validate_ip(ip_address):
            QMessageBox.warning(dialog, "错误", "请输入有效的IP地址！")
            return

        if not self.selected_file:
            QMessageBox.warning(dialog, "错误", "请选择传输文件！")
            return

        self.selected_solution = solution_num
        dialog.accept()

        # 写入data.txt文件
        start_region = self.start_combo.currentText()
        end_region = self.end_combo.currentText()
        selected_path = self.result_paths[solution_num]
        print(selected_path)
        with open("data.txt", "w", encoding='utf-8') as f:
            f.write(f"Region: {selected_path}\n")
            f.write(f"IP: {ip_address}\n")
        file_name = os.path.basename(self.selected_file)
        print(file_name)

        # 显示传输确认对话框
        self.show_transfer_confirmation()

    def validate_ip(self, ip):
        """简单的IP地址验证"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def show_transfer_confirmation(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("确认传输")
        msg_box.setText("是否开始传输数据？")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        # 设置按钮样式
        msg_box.setStyleSheet("""
            QPushButton {
                min-width: 80px;
                min-height: 30px;
                padding: 5px;
            }
            QPushButton#yesButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#noButton {
                background-color: #f44336;
                color: white;
            }
        """)

        # 获取按钮并设置对象名用于样式
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setObjectName("yesButton")
        no_button = msg_box.button(QMessageBox.No)
        no_button.setObjectName("noButton")

        reply = msg_box.exec_()

        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "成功", "传输已开始！")
            subprocess.run(['python', "yml.py"], capture_output=True, text=True,
                                      cwd=r'C:\Users\22748\Desktop\chuanshu\cloudsstorm\Infs\Topology',encoding='utf-8')
            print("已更新配置文件")
            time.sleep(1)
            subprocess.Popen(['java', '-jar', './CloudsStorm-2.0.jar', 'execute', './'],
                                        cwd=r"C:\Users\22748\Desktop\chuanshu\cloudsstorm",encoding='utf-8')
            time.sleep(10)
            subprocess.run(['python', "get_ip.py"],
                                      cwd=r"C:\Users\22748\Desktop\chuanshu",encoding='utf-8')
            ip_list = []
            with open(r'C:\Users\22748\Desktop\chuanshu\output.txt', 'r') as file:
                for line in file:
                    ip_list.append(line.strip())
            print("ip_list: ", ip_list)
            command = ['python', '1_a.py', '-n', str(len(ip_list)), '-ip']
            for ip in ip_list:
                command.append(ip)
            print(command)
            subprocess.run(command, cwd=r"C:\Users\22748\Desktop\chuanshu",encoding='utf-8')
        else:
            QMessageBox.information(self, "取消", "传输已取消。")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())