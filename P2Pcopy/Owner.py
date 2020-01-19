# encoding:utf-8
from common import P2PServer
import argparse
import sys


class Owner(P2PServer):
    def __init__(self, share_file: str, work_dir: str = 'owner', server_name: str = 'Owner'):
        super().__init__(server_name=server_name, work_dir=work_dir)
        if not self.file_split(share_file):
            sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-P', '--port', help='Server port')
    parser.add_argument('-F', '--file', help='File to share')
    args = parser.parse_args()

    # 用待传送文件初始化, 这里Owner会对文件做分割等操作
    owner = Owner(args.file)
    # 启动服务端
    owner.listen(server_port=int(args.port))
