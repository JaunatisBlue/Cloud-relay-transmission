# 多云中转车辆数据传输原型

本项目是一个用于选拔赛演示的多云中转传输原型。系统通过前端界面选择起点、终点和传输方案，使用云资源编排工具创建中间节点，再把 `db/A` 中的数据切片、多路发送到中转节点，最终在接收端合并到 `db/C`。部分中转脚本还集成了 OpenCV 车辆检测处理逻辑。

## 功能概览

- 传输路径评估：根据区域价格、带宽和链路速率计算低成本、速率约束、最高速等方案。
- 图形界面：使用 PyQt5 选择起点、终点、待传输文件和接收端 IP。
- 云资源编排：通过 CloudsStorm 的 YAML 配置创建 EC2/Aliyun 节点，并执行节点初始化脚本。
- 多路传输：发送端把文件切成 512 KB 左右的数据片，多线程分发到多个中转节点。
- 断点续传：接收端检查 `cache/<filename>/` 中已有分片，向发送端返回下一个缺失分片编号。
- 文件合并：接收端保存分片后按序合并到 `db/C/<filename>`。
- 视频处理：`b1.py`、`b2.py`、`b3.py`、`b4.py` 中包含基于 `cars.xml` 的车辆检测和视频输出逻辑。

## 目录结构

```text
.
├── qianduan.py                 # PyQt5 前端入口，负责方案选择和启动传输流程
├── example.py                  # 路径方案计算示例入口
├── node_select.py              # 路径/节点选择算法
├── node_select_1.py            # 节点价格、带宽、链路速率数据填充
├── 1_a.py                      # A 端发送脚本，读取 db/A/A.zip 并多线程发送
├── 3_c.py                      # C 端接收服务，保存分片并合并文件
├── b.py                        # 基础中转节点，监听 4026 并转发到 C 端 6000
├── b1.py ~ b4.py               # 带车辆检测处理的中转节点变体
├── duan.py                     # 断点续传握手转发脚本
├── get_ip.py                   # 从 CloudsStorm 日志提取公网 IP 到 output.txt
├── conf/                       # A/B/C 端配置和日志配置
├── lib/common.py               # 日志初始化工具
├── db/
│   ├── A/                      # 发送端数据目录
│   └── C/                      # 接收端输出目录
├── cache/                      # 接收端临时分片目录
├── log/                        # Python 运行日志
├── cloudsstorm/
│   ├── CloudsStorm-2.0.jar     # 云资源编排工具
│   ├── App/infrasCode.yml      # CloudsStorm 执行流程配置
│   └── Infs/Topology/          # 云拓扑、虚拟机和初始化脚本
├── cars.xml                    # OpenCV 车辆检测级联分类器
└── data.txt                    # 前端写入的路径和接收端 IP
```

## 运行环境

建议使用 Python 3.9+。仓库中没有 `requirements.txt`，按源码导入关系需要安装以下依赖：

```bash
pip install PyQt5 PyYAML filelock opencv-python numpy matplotlib
```

如果运行 `ccccc.py` 中的深度学习道路检测逻辑，还需要额外准备：

```bash
pip install torch torchvision
```

同时该脚本引用了 `networks.unet`、`networks.dunet`、`networks.dinknet`，当前目录未包含 `networks/` 模块，直接运行会报错，需要补齐模型代码和权重。

云资源编排依赖：

- Java 运行环境，用于执行 `cloudsstorm/CloudsStorm-2.0.jar`。
- CloudsStorm 所需云账号配置，见 `cloudsstorm/Infs/UC/` 与 `cloudsstorm/Infs/UD/`。
- 云端虚拟机需要能执行 `python3 b.py -ip <接收端IP>` 等命令，并开放相应端口。

## 典型使用流程

### 1. 启动接收端

在最终接收机器上运行：

```bash
python 3_c.py
```

默认监听：

- `0.0.0.0:6000`
- 功能码 `1`：断点续传查询
- 功能码 `0`：接收分片数据

接收完成后，文件会合并到：

```text
db/C/<filename>
```

### 2. 通过前端选择方案

运行：

```bash
python qianduan.py
```

界面会执行以下逻辑：

1. 选择起点区域和终点区域。
2. 调用 `example.road()` 生成三类传输方案。
3. 选择待传输文件和接收端 IP。
4. 把选择结果写入 `data.txt`。
5. 调用 `cloudsstorm/Infs/Topology/yml.py` 生成拓扑 YAML。
6. 调用 `CloudsStorm-2.0.jar` 创建云节点并执行中转节点脚本。
7. 从 CloudsStorm 日志提取中转节点公网 IP。
8. 调用 `1_a.py` 发送文件。

### 3. 直接运行发送端

如果已经有中转节点 IP，可以跳过前端，直接运行：

```bash
python 1_a.py -n 2 -ip <node-ip-1> <node-ip-2>
```

当前 `1_a.py` 默认发送：

```text
db/A/A.zip
```

发送端会先连接 C 端的 `6000` 端口做断点查询，然后连接每个中转节点的 `4026` 端口分发数据。

### 4. 启动中转节点

基础中转：

```bash
python b.py -ip <C端公网IP>
```

默认行为：

- 监听 `0.0.0.0:4026`
- 收到 A 端数据后连接 `<C端公网IP>:6000`
- 转发文件头和分片数据

带车辆检测的中转节点可使用 `b1.py`、`b2.py`、`b3.py`、`b4.py`，但这些脚本对本地目录和端口有更多假设，运行前需要确认 `received_images/`、`result_mp4s/` 等目录存在。

## 路径选择模型

`example.py` 内置了区域列表、云服务器价格、最大带宽和区域间测速矩阵。`road(source, des)` 会返回：

- `result1`：最低成本方案。
- `result2`：满足最低速率约束的低成本方案。
- `result3`：按速率优先的方案。

计算逻辑位于：

- `node_select.py`
- `node_select_1.py`

数据量默认写死为：

```python
data_size = 56900 * 8
```

如需匹配真实文件大小，应在调用前按文件体积重新计算。

## 配置说明

`conf/settings_a.py`、`conf/settings_b.py`、`conf/settings_c.py` 分别定义 A/B/C 端默认目录和端口：

```python
IP = "127.0.0.1"
PORT = 8000 / 8005
DB_PATH = <project>/db
CLIENT_DB_PATH = <project>/db/A|B|C
SERVER_DB_PATH = <project>/db/A|B|C
LOG_PATH = <project>/log
```

实际传输脚本中还有一些独立端口：

| 脚本 | 默认端口 | 用途 |
| --- | --- | --- |
| `3_c.py` | `6000` | C 端接收和断点查询 |
| `b.py` | `4026` | 基础中转节点 |
| `b1.py` | `4026` | 车辆检测中转变体 |
| `b2.py`、`b3.py`、`b4.py` | `4027` | 车辆检测中转变体 |
| `duan.py` | `5026` | 断点续传握手转发 |

## 已知限制和注意事项

- 多个脚本包含硬编码路径，例如 `C:\Users\22748\Desktop\chuanshu`。在其他机器运行前，需要把 `qianduan.py`、`get_ip.py`、`cloudsstorm/Infs/Topology/yml.py` 中的绝对路径改为当前项目路径。
- `1_a.py` 中硬编码了一个 C 端地址 `35.76.1.177:6000`，实际部署时需要改为当前接收端地址，或改造成命令行参数。
- 仓库中包含 `cloudsstorm/Infs/Topology/*/id_rsa` 等私钥文件。正式提交或共享前应删除并轮换相关密钥。
- `cloudsstorm/Infs/Topology/venv/` 是已生成的虚拟环境，不建议纳入版本管理。
- `log/`、`cache/`、`__pycache__/`、`output.mp4` 等属于运行产物，可按需清理。
- 当前代码没有自动化测试，也没有统一依赖锁定文件。
- 部分源码注释和界面文本存在编码异常，但不影响主要逻辑阅读。

## 建议的后续整理

- 新增 `requirements.txt`。
- 把绝对路径、云端 IP、文件名、端口统一迁移到配置文件或命令行参数。
- 删除仓库中的私钥、日志、虚拟环境和缓存文件，并补充 `.gitignore`。
- 将发送端、中转端、接收端协议封装成独立模块，减少 `1_a.py`、`b*.py`、`3_c.py` 之间的重复逻辑。
- 为 `node_select.py` 的路径选择算法补充单元测试。
