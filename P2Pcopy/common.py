# encoding:utf-8
from threading import RLock, Thread
from datetime import datetime
from socket import *
import json
import os
import shutil


class FileOperation:
    def __init__(self, work_dir: str, chunk_size: int = 102400):
        # 缓存文件存储目录, 便于不同节点指定不同缓存目录, 以防出现文件同名冲突
        self.cache_path = work_dir
        # 分割后的文件大小, 默认100KB
        self.chunk_size = chunk_size
        # 记录文件块数据
        self.file_parts = {}
        # 记录要传递的文件名
        self.filename = None

    def file_split(self, file: str):
        """
        :param file: 待分割文件
        :return:
        """
        if not os.path.isfile(file):
            print("File doesn't exist")
            return False

        # 重建存储目录
        if os.path.isdir(self.cache_path):
            shutil.rmtree(self.cache_path)
        os.mkdir(self.cache_path)

        # 获得文件名
        file_abspath = os.path.abspath(file)
        file_dirname, file_name = os.path.split(file_abspath)
        self.filename = file_name

        # 分割文件, 从源文件中循环读取指定大小的数据, 增加part后缀并写入存储目录
        with open(file_abspath, mode='br') as source:
            part = 0
            while True:
                temp = source.read(self.chunk_size)
                if not temp:
                    break

                part += 1
                target = os.path.abspath(os.path.join(self.cache_path, f"{file_name}.part{part}"))
                target_file = open(target, mode='ba')
                target_file.write(temp)
                target_file.close()

                self.file_parts[str(part)] = target
        return True

    def file_merge(self, target: str):
        """
        :param target: 文件合并后存储的路径
        :return:
        """
        # 目标文件已存在则删除
        if os.path.isfile(target):
            os.remove(target)

        with open(target, mode='ba') as target_file:
            # 获取文件分割详情表, 并写入目标文件
            part_files_sort = sorted(self.file_parts.keys(), key=lambda item: int(item))
            for part_index in part_files_sort:
                file_part = open(self.file_parts.get(part_index), mode='br')
                content = file_part.read()
                target_file.write(content)
                file_part.close()


class P2PServer(FileOperation):
    def __init__(self, server_name: str, work_dir: str):
        super().__init__(work_dir=work_dir)

        # 服务器名称, 用于识别服务端
        self.name = server_name

        # 服务端最大连接数
        self.max_clients = 10

        # 服务端数据接受字节数, 默认1KB
        self.recv_size = 1024

        # 锁, 避免print内容出现混淆
        self.lock_timeout = 10
        self.lock = RLock()

    def listen(self, server_port: int):
        # 启动监听
        server = socket(AF_INET, SOCK_STREAM)
        server.bind(('0.0.0.0', server_port))
        server.listen(self.max_clients)
        print(f'{datetime.now()} - {self.name} - Server "{self.name}" Listen on ":{server_port}"...')

        while True:
            # 获取连接
            conn, addr = server.accept()
            self.lock.acquire(timeout=self.lock_timeout)
            print(f'{datetime.now()} - {self.name} - Accept Client: {addr}')
            self.lock.release()

            # 接受客户端指令
            # 指令分为两类
            # ① part: part_id, 服务端接受此类指令, 则发送对应id的文件切片
            # ② hash, 服务端接受该命令, 则发送文件切片的MD5数据
            recv = conn.recv(self.recv_size).decode('utf-8')
            if recv[:4] == 'part':
                part_id = int(recv[6:])
                thread = Thread(target=self.send_file_part, args=(conn, part_id, addr))
                thread.setDaemon(True)
                thread.start()
            elif recv == 'FileBlockList':
                thread = Thread(target=self.send_hash, args=(conn, addr))
                thread.setDaemon(True)
                thread.start()
            elif recv == 'filename':
                conn.sendall(self.filename.encode())
            else:
                print(f'{datetime.now()} - {self.name} - Unknown Command: {recv}')

    def send_file_part(self, conn: socket, part: int, addr: tuple):
        self.lock.acquire(timeout=self.lock_timeout)
        print(f"{datetime.now()} - {self.name} - Client {addr} - Send File Part {part} - sending...")
        self.lock.release()

        # 读取对应的文件分片并发送
        part_name = self.file_parts.get(str(part))
        content = open(part_name, mode='br').read()
        conn.sendall(content)
        conn.close()

        self.lock.acquire(timeout=self.lock_timeout)
        print(f"{datetime.now()} - {self.name} - Client {addr} - Send File Part {part} - finished")
        self.lock.release()

    def send_hash(self, conn: socket, addr: tuple):
        self.lock.acquire(timeout=self.lock_timeout)
        print(f"{datetime.now()} - {self.name} - Client {addr} - Send File Hash - sending...")
        self.lock.release()

        # 发送切片文件的MD5
        conn.sendall(json.dumps(list(self.file_parts.keys())).encode('utf-8'))
        conn.close()

        self.lock.acquire(timeout=self.lock_timeout)
        print(f"{datetime.now()} - {self.name} - Client {addr} - Send File Hash - finished")
        self.lock.release()
