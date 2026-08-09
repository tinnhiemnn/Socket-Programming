# Hybrid FTP System: Reliable Data Transfer (RDT) over UDP with TCP Control

An advanced **Hybrid File Transfer Protocol (Hybrid FTP)** implementation developed for the Computer Networks course at the Faculty of Information Technology, University of Science, Vietnam National University - Ho Chi Minh City (FIT-VNUHCM).

The system architecture combines the stability of **TCP for the Control Channel** with a custom **Reliable Data Transfer (RDT) protocol over UDP for the Data Channel**.



## 🛈 Overview

Traditional FTP (RFC 959) relies entirely on TCP for both control messages and data transfer. **Hybrid FTP** decouples these operations across two transport-layer protocols:

1. **TCP Control Channel (Port 2121):** Handles session initialization, user authentication, directory navigation, and mode configuration. TCP guarantees reliable, ordered command delivery.


2. **UDP Data Channel with Custom RDT:** Handles file downloads, uploads, and directory listings. Since raw UDP is unreliable, a custom application-layer **Stop-and-Wait ARQ** protocol with 16-bit Internet Checksums, sequence numbers, timeouts, and automatic retransmissions ensures 100% data integrity.



## ✨ Key Features

* **Zero External Dependencies:** Built **100% using the Python Standard Library** (`socket`, `threading`, `struct`, `getpass`, `signal`, `os`, `sys`, `time`). No `pip install` required!
* **Custom UDP Reliable Data Transfer (RDT):**
    * **Stop-and-Wait ARQ:** Synchronous packet delivery with acknowledgement tracking.


    * **Error Detection:** 16-bit 1's Complement Internet Checksum (RFC 1071).


    * **Packet Loss Handling:** Retransmission timer with configurable `MAX_RETRIES`.


    * **Boundary Integrity:** 10-Byte fixed header parsing to prevent byte drift.




* **Data Modes & Types:**
    * **Passive (PASV) & Active (PORT) Modes** for firewall/NAT flexibility.


    * **Binary (TYPE I)** and **ASCII (TYPE A)** transfer modes.




* **Multi-Client Concurrent Support:** Threaded `ClientHandler` execution with isolated session states protected by `threading.Lock()`.


* **Interactive Server Console:** Real-time active session monitoring (`sessions`, `status`) and clean shutdown via `Ctrl+C`.


* **User-Friendly Client CLI:** Native progress bars using `\r` line-overwriting, ANSI color logs, and hidden password input via `getpass`.



## 📁 Project Directory Structure

```text
Socket-Programming/
├── client/
│   ├── __init__.py
│   ├── cli_formatter.py     # ANSI color formatting & UI utilities
│   ├── client_core.py       # FTP Client protocol handling logic
│   ├── client_data.py       # RDT data transmission handler for Client
│   └── main.py              # Client CLI interactive terminal entrypoint
├── server/
│   ├── __init__.py
│   ├── main.py              # Server startup & signal listener entrypoint
│   ├── server_core.py       # Multi-threaded ClientHandler & command parser
│   └── server_data.py       # RDT UDP sender/receiver & session logger
├── shared/
│   ├── protocol.py          # FTP response codes & shared constants
│   ├── rdt_data_channel.py  # Core RDT Stop-and-Wait ARQ implementation
│   └── rdt_packet.py        # Custom Header builder & 16-bit Checksum
├── storage/                 # Storage directory for server/client files
└── README.md                # Project documentation

```



## 🛠 Prerequisites

* **Python:** Python `3.10` or higher (Tested on Python `3.13.1` on Windows 11 / Linux).


* **Dependencies:** None. All modules belong to the Python Standard Library.



## 🚀 Installation & Execution

Clone the repository to your local machine:

```bash
git clone https://github.com/tinnhiemnn/Socket-Programming.git
cd Socket-Programming

```

### 1. Starting the FTP Server

Run the server main entrypoint:

```bash
python server/main.py

```

The server will bind to `0.0.0.0:2121` and start listening for TCP control connections:

```text
[SYSTEM] [+] FTP Server initialized successfully. Listening on TCP 0.0.0.0:2121...
[SYSTEM] [*] Server CLI Console ready. Type 'help' or 'sessions' for commands.

```

To stop the server at any time, press `Ctrl + C`.

### 3. Running the FTP Client

Open a separate terminal window and launch the client:

```bash
python client/main.py

```

Default connection target is `127.0.0.1:2121`.



## 💻 Usage Workflow

1. **Authentication:**
Upon connecting, log in with the default server credentials:


* **Username:** `admin`

* **Password:** `123456` *(input is hidden automatically using `getpass`)*



2. **Check Directory & Navigation:**
```text
ftp-client [PASV|TYPE-I]> PWD
257 "/" is the current directory.

ftp-client [PASV|TYPE-I]> LIST
Fetching directory listing (LIST) via UDP RDT...
drwxr-xr-x    1       owner    group    0               folder_1
-rw-r--r--    1       owner    group    13843           sample.png
226 Transfer complete.

```


3. **Download a File (RETR):**
```text
ftp-client [PASV|TYPE-I]> RETR sample.png E:/local_sample.png
Downloading 'sample.png' via UDP RDT...
Donwloading:    2.1 MB received | Speed:    1.0 MB/s
Data transmission has ended. Reception complete!
226 Transfer complete.

```


4. **Upload a File (STOR):**
```text
ftp-client [PASV|TYPE-I]> STOR E:/my_document.pdf document.pdf
Uploading 'E:/my_document.pdf' via UDP RDT...
Progress: [████████████████████████████████] 100.00% |    15.9 KB / 15.9 KB  | Speed:   2.1 MB/s
All data has been transferred securely!
226 Transfer complete.

```


5. **Switching Modes & Types:**
* Switch to Active Mode: `PORT`

* Switch to Passive Mode: `PASV`

* Switch to ASCII Mode: `TYPE A`

* Switch to Binary Mode: `TYPE I`





## 👥 Authors & Copyright

### Development Team

* **Trang Tín Nhiệm** (`25127003`)

* **Nguyễn Trần Kim Cương** (`25127023`)

* **ThS. Huỳnh Thụy Bảo Trân** - Instructor

* **ThS. Chung Thùy Linh** - Instructor

### Copyright

Copyright © 2026 FIT VNUHCM-US. All rights reserved.

This project was developed as part of the **Computer Networks** course at the Faculty of Information Technology, VNUHCM - University of Science.

