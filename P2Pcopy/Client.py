# encoding:utf-8
from common import P2PServer, Thread, datetime
from socket import *
import argparse
import os
import json


class Client(P2PServer):
    def __init__(self, client_id: int, owner_host: str, neighbor_host: str):
        super().__init__(work_dir=f"client_{client_id}", server_name=f"Client_{client_id}")
        self.client_id = client_id
        self.owner_host = owner_host
        self.neighbor_host = neighbor_host
        if not os.path.isdir(self.cache_path):
            os.mkdir(self.cache_path)

    @staticmethod
    def write_file(file_path: str, content: bytes):
        file_dirname, file_name = os.path.split(file_path)
        if not os.path.isdir(file_dirname):
            os.mkdir(file_dirname)
        if os.path.isfile(file_path):
            os.remove(file_path)
        with open(file_path, mode='ba') as f:
            f.write(content)

    def recv(self, conn: socket, decode: bool = False):
        response = ''.encode()
        while True:
            rec = conn.recv(self.recv_size)
            response += rec
            if len(rec) < self.recv_size:
                break
        return response if not decode else response.decode()

    def request(self, host: str, base_name: str, part_id: int = None):
        ip, port = host.split(':')
        conn = socket(AF_INET, SOCK_STREAM)
        conn.connect((ip, int(port)))

        command = f"part: {part_id}" if part_id else 'FileBlockList'
        conn.sendall(command.encode())
        decode = False if part_id else True
        content = self.recv(conn, decode)
        peer = conn.getpeername()
        conn.close()

        if part_id:
            part_file_path = os.path.abspath(os.path.join(self.cache_path, f"./{base_name}.part{part_id}"))
            self.write_file(file_path=part_file_path, content=content)
            print(f'{datetime.now()} - {self.name} - Get File Part {part_id} from {peer}')
            self.file_parts[str(part_id)] = part_file_path
            return None
        else:
            file_parts = json.loads(content)
            file_path = os.path.abspath(os.path.join(self.cache_path, './file_block_list.json'))
            if os.path.isfile(file_path):
                os.remove(file_path)
            json.dump(file_parts, open(file_path, mode='a'))
            print(f'{datetime.now()} - {self.name} - Get File Hash From {peer}')
            return file_parts

    def run(self, save_filename: str, clients_num: int = 5):
        owner_file_parts = self.request(host=self.owner_host, base_name=save_filename)
        total_parts = len(owner_file_parts)
        part_id = [int(item) for item in owner_file_parts if int(item) % clients_num + 1 == self.client_id]
        for part in part_id:
            self.request(host=self.owner_host, base_name=save_filename, part_id=part)

        while True:
            try:
                neighbor_parts = self.request(host=self.neighbor_host, base_name=save_filename)
                rest_ids = set(neighbor_parts) - set(self.file_parts.keys())
                for part_id in rest_ids:
                    self.request(host=self.neighbor_host, base_name=save_filename, part_id=int(part_id))
                    self.file_parts[part_id] = os.path.abspath(os.path.join(
                        self.cache_path, f"./{save_filename}.part{part_id}"
                    ))
                if len(self.file_parts) == total_parts:
                    print(f'{datetime.now()} - {self.name} - All File Part has existed')
                    self.file_merge(target=os.path.abspath(os.path.join(
                        self.cache_path, save_filename
                    )))
                    print(f"{datetime.now()} - {self.name} - File Merge Finished")
                    break
            except Exception:
                print(f"{datetime.now()} - {self.name} - Neighbor '{self.neighbor_host}' is not running.")

def run_client(client_id: int, server_port: int, neighbor_host: str, file_save_name: str, owner_host='127.0.0.1:5000'):
    client = Client(client_id=client_id, owner_host=owner_host, neighbor_host=neighbor_host)
    download_thread = Thread(target=client.run, args=(file_save_name,))
    download_thread.start()
    client.listen(server_port=server_port)

if __name__ == '__main__':
    parse = argparse.ArgumentParser()
    parse.add_argument('-i', '--client-id', help='Client ID')
    parse.add_argument('-p', '--server-port', help='Peer Server Port')
    parse.add_argument('-n', '--neighbor-host', help='Neighbor Host')
    parse.add_argument('-f', '--save-name', help='File Name To Save')
    parse.add_argument('-o', '--owner-host', help='Owner Server Host')
    args = parse.parse_args()
    run_client(
        client_id=int(args.client_id),
        server_port=int(args.server_port),
        neighbor_host=args.neighbor_host,
        file_save_name=args.save_name,
        owner_host=args.owner_host
    )
