# Multi-Cloud Relay Data Transmission Prototype
This project implements a multi-cloud relay transmission prototype. Via the front-end GUI, users select the data source, destination, and transmission scheme. Cloud resource orchestration tools are leveraged to create intermediate relay nodes. The system slices data files stored in `db/A`, distributes data chunks to relay nodes through multi-stream parallel transmission, and finally reassembles all chunks on the receiving side into complete files saved under `db/C`. Selected relay scripts integrate OpenCV-based vehicle detection pipelines for video processing.

## Core Function Overview
1. Transmission Path Evaluation
Calculate three types of transmission schemes based on regional cloud pricing, available bandwidth, and inter-region link throughput: lowest-cost paths, low-cost paths meeting minimum throughput constraints, and maximum-throughput priority paths.
2. Graphical User Interface
Built with PyQt5; supports selection of source/destination regions, target files for transmission, and receiving server public IP addresses.
3. Cloud Resource Orchestration
Provision AWS EC2 and Alibaba Cloud virtual machines via CloudsStorm YAML configuration files, and automatically execute initialization scripts on newly created cloud nodes.
4. Multi-Stream Parallel Transmission
The sender splits source files into ~512 KB fixed-size chunks and dispatches chunks to multiple relay nodes using multi-threaded workers.
5. Resume Interrupted Transfers
The receiver scans existing partial chunks under `cache/<filename>/` and replies to the sender with the serial number of the next missing chunk to resume incomplete transfers.
6. File Reassembly
After receiving all fragmented data, the receiver sorts chunks by sequence number and merges them into a complete file stored at `db/C/<filename>`.
7. Video Stream Processing
Scripts `b1.py` to `b4.py` embed vehicle detection logic using the `cars.xml` Haar cascade classifier and support processed video export.

## Project Directory Structure
```text
.
├── qianduan.py                 # PyQt5 front-end entry; triggers full transmission workflow after scheme selection
├── example.py                  # Entry script for path planning and transmission scheme calculation demos
├── node_select.py              # Core algorithm for transmission path and relay node selection
├── node_select_1.py            # Populates static metadata: cloud node pricing, bandwidth limits, inter-region link throughput
├── 1_a.py                      # Sender-side script; reads source file db/A/A.zip and dispatches chunks via multi-threading
├── 3_c.py                      # Receiver service; stores fragmented data and executes full file reassembly
├── b.py                        # Base relay node service; listens on port 4026 and forwards all data to the receiver’s port 6000
├── b1.py ~ b4.py               # Extended relay variants integrated with OpenCV vehicle detection pipelines
├── duan.py                     # Forwarding script dedicated to resume-transfer handshake signaling
├── get_ip.py                   # Parses CloudsStorm orchestration logs and exports relay node public IPs to output.txt
├── conf/                       # Configuration files for sender(A), relay(B), receiver(C), and logging rules
├── lib/common.py               # Reusable logging initialization utility module
├── db/
│   ├── A/                      # Local storage directory for source files on the sending side
│   └── C/                      # Output directory for fully reassembled files on the receiving side
├── cache/                      # Temporary storage for incomplete file chunks on the receiver
├── log/                        # Runtime log directory for all Python modules
├── cloudsstorm/
│   ├── CloudsStorm-2.0.jar     # Java-based cloud resource orchestration engine
│   ├── App/infrasCode.yml      # Main YAML workflow definition for CloudsStorm provisioning
│   └── Infs/Topology/          # Cloud topology definitions, VM provision templates, and node initialization scripts
├── cars.xml                    # Haar cascade classifier pre-trained for OpenCV vehicle detection
└── data.txt                    # Intermediate file storing user-selected path parameters and receiver IP exported by the GUI
```

## Runtime Environment
Python 3.9 or higher is recommended. No pre-generated `requirements.txt` is provided in the repository; install core dependencies matching import statements with the following command:
```bash
pip install PyQt5 PyYAML filelock opencv-python numpy matplotlib
```
If executing deep learning road detection logic inside `ccccc.py`, install additional AI dependencies:
```bash
pip install torch torchvision
```
This script references custom network modules `networks.unet`, `networks.dunet`, and `networks.dinknet.` The `networks/` folder and pre-trained weight files are not included in the repository, which will throw runtime errors if missing.

### Dependencies for Cloud Orchestration
1. Java Runtime Environment to execute the orchestration JAR `cloudsstorm/CloudsStorm-2.0.jar`
2. Valid cloud account credentials configured under `cloudsstorm/Infs/UC/` and `cloudsstorm/Infs/UD/`
3. Cloud virtual machines must allow inbound Python services and open designated TCP ports for data transmission; nodes must support running commands such as `python3 b.py -ip <RECEIVER_PUBLIC_IP>`

## Standard End-to-End Workflow
### Step 1: Launch the Receiver Service
Execute this command on the target receiving server:
```bash
python 3_c.py
```
Default listening address: `0.0.0.0:6000`
- Function Code `1`: Handles resume-transfer chunk existence queries
- Function Code `0`: Receives raw file data chunks
After full transmission completes, the merged complete file is saved to:
```text
db/C/<filename>
```

### Step 2: Select Transmission Scheme via Front-End GUI
Launch the graphical interface:
```bash
python qianduan.py
```
The GUI automates the following sequence:
1. User selects source cloud region and destination cloud region
2. Calls `example.road()` to generate three distinct transmission schemes
3. User selects the source file to transmit and inputs the receiver’s public IP
4. Serializes all user selections into the intermediate file `data.txt`
5. Invokes `cloudsstorm/Infs/Topology/yml.py` to auto-generate cloud topology YAML templates
6. Executes CloudsStorm JAR to provision cloud relay nodes and deploy relay initialization scripts
7. Extracts all relay node public IP addresses from orchestration logs
8. Triggers the sender script `1_a.py` to start parallel chunk transmission

### Step 3: Direct Sender Launch (Bypassing GUI)
If relay node IP addresses are already known, skip the front-end and run the sender directly:
```bash
python 1_a.py -n 2 -ip <relay-node-ip-1> <relay-node-ip-2>
```
By default, `1_a.py` transmits the fixed source file:
```text
db/A/A.zip
```
The sender first establishes a handshake connection to port 6000 of the receiver to query completed chunks for resume support, then connects to port 4026 of every relay node to dispatch data chunks.

### Step 4: Start Relay Node Services
#### Base Relay Node (No Video Processing)
```bash
python b.py -ip <RECEIVER_PUBLIC_IP>
```
Default behavior:
- Listens for incoming sender connections on `0.0.0.0:4026`
- Establishes an outbound connection to `<RECEIVER_PUBLIC_IP>:6000` upon receiving data
- Forwards file header metadata and all raw data chunks to the final receiver

#### Vehicle-Detection Extended Relays
Use `b1.py`, `b2.py`, `b3.py`, or `b4.py` for video processing pipelines. These scripts require pre-created local directories `received_images/` and `result_mp4s/` to store detection outputs before execution.

## Path Planning Model Details
`example.py` contains static metadata tables: available cloud regions, per-region VM pricing, maximum egress bandwidth, and pre-measured inter-region link throughput matrices. The core function `road(source, destination)` returns three alternative transmission plans:
1. `result1`: Minimum monetary cost transmission path
2. `result2`: Lowest-cost path satisfying user-specified minimum throughput constraints
3. `result3`: Maximum throughput priority path, ignoring cost overhead

Calculation logic is split across two modules:
- `node_select.py`: Main optimization logic for path cost and throughput tradeoff
- `node_select_1.py`: Static data lookup table for cloud infrastructure parameters

The default data volume constant is hardcoded as:
```python
data_size = 56900 * 8
```
Replace this value with the actual target file byte size before running path evaluation for real-world transmission tasks.

## Global Configuration Specifications
Files `conf/settings_a.py`, `conf/settings_b.py`, `conf/settings_c.py` define core static parameters for sender, relay, and receiver respectively:
```python
IP = "127.0.0.1"
PORT = 8000 / 8005
DB_PATH = <PROJECT_ROOT>/db
CLIENT_DB_PATH = <PROJECT_ROOT>/db/A|B|C
SERVER_DB_PATH = <PROJECT_ROOT>/db/A|B|C
LOG_PATH = <PROJECT_ROOT>/log
```
Additional dedicated TCP ports hardcoded within individual transmission scripts are listed below:
| Script File | Default Listening Port | Function Description |
| --- | --- | --- |
| `3_c.py` | `6000` | Receiver service for chunk reception and resume handshake |
| `b.py` | `4026` | Standard base relay data forwarding service |
| `b1.py` | `4026` | Relay service integrated with vehicle detection pipeline |
| `b2.py`, `b3.py`, `b4.py` | `4027` | Extended video-processing relay variants |
| `duan.py` | `5026` | Dedicated forwarding service for resume-transfer signaling |

## Known Limitations & Critical Warnings
1. Hardcoded absolute Windows file paths exist in multiple core scripts (e.g. `C:\Users\22748\Desktop\chuanshu`). Modify hardcoded paths in `qianduan.py`, `get_ip.py`, and `cloudsstorm/Infs/Topology/yml.py` to match the target deployment environment before cross-platform execution.
2. `1_a.py` embeds a static receiver endpoint `35.76.1.177:6000`. Rewrite this as a command-line argument parameter or load it from configuration files for flexible cross-environment deployment.
3. Sensitive private key files such as `cloudsstorm/Infs/Topology/*/id_rsa` are stored in the repository. Delete and regenerate all cloud authentication keys before code sharing or formal submission.
4. The directory `cloudsstorm/Infs/Topology/venv/` stores a pre-built Python virtual environment; exclude this folder from version control systems.
5. Runtime-generated artifacts including `log/`, `cache/`, `__pycache__/`, and output video files such as `output.mp4` can be safely deleted to clean workspace storage.
6. No automated unit test suites are implemented for core path planning and transmission modules.
7. Minor garbled character encoding issues exist in inline code comments and GUI text labels, which do not interfere with core program logic.

## Recommended Subsequent Code Refactoring Tasks
1. Create a standardized `requirements.txt` file to lock all Python dependency versions
2. Migrate all hardcoded absolute file paths, cloud public IP addresses, default filenames, and TCP port numbers into unified configuration files or parseable command-line arguments
3. Remove sensitive private keys, runtime logs, virtual environments, and cache folders from version control; add a complete `.gitignore` template
4. Encapsulate sender, relay, and receiver transmission communication protocols into reusable independent modules to eliminate duplicate logic across `1_a.py`, all `b*.py` variants, and `3_c.py`
5. Develop unit test cases to validate the correctness of the path planning algorithm inside `node_select.py`
