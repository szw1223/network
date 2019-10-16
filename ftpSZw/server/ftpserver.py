"""
File:   Project01.py
Author:  Zhewei Song
Date: 10th Oct 2019
Desc: Hello, this is server program.

"""
""" =======================  Import dependencies ========================== """
import socket
from threading import Thread
import os

""" =======================  Set address and user info ========================== """
host = '127.0.0.1'
port = 5000

userInfo = [{'username': 'user00', 'password': 'user00'},
			{'username': 'user01', 'password': 'user01'},
			{'username': 'user02', 'password': 'user02'}]

""" =======================  Receive File function ========================== """
def receiveFile(msg, client):
	fileName = msg.split(b"|$|")[1].decode()
	filesize = int(msg.split(b"|$|")[2].decode())
	writer = open(fileName, "wb")
	write_data = msg.split(b"|$|")[3]
	writer.write(write_data)
	buff_size = 1024
	rest_size = filesize - len(write_data)
	if rest_size <= 0:
		pass
	elif rest_size > buff_size:
		buff_size = rest_size
		recv_data = client.recv(buff_size)
		rest_size -= buff_size
		while rest_size>0:
			writer.write(recv_data)
			if rest_size >= 1024:
				recv_data = client.recv(1024)
				rest_size -= 1024
			else:
				recv_data = client.recv(rest_size)
				rest_size = 0
		writer.write(recv_data)
	else:
		recv_data = client.recv(buff_size)
		writer.write(recv_data)
	writer.close()
	print("Server has received ", fileName)

""" =======================  Handle Info function ========================== """
def  handleClient(client, address):
	while True:
		msg = client.recv(1024)
		fileList = os.listdir()
		if msg.startswith(b"login"):
			msg = msg.decode()
			input_username = msg.split("|$|")[1]
			input_password = msg.split("|$|")[2]
			login_success = False
			for item in userInfo:
				if input_username == item['username'] and input_password == item['password']:
					login_success = True
					break
			if login_success:
				client.send("success".encode())
			else:
				client.send("fail".encode())
		elif msg.startswith(b"dir"):
			client.send(" ".join(fileList).encode())
		elif msg.startswith(b"get"):
			fileName = msg.split(b"|$|")[1].decode()
			try:
				with open(fileName, 'rb') as f:
					filesize = len(f.read())
				reader = open(fileName, 'rb')
				send_data = reader.read(1017 - len(str(filesize)) - 3)
				client.send(("success"+str(filesize)+"|$|").encode()+send_data)
				send_data = reader.read(1024)
				while send_data:					
					client.send(send_data)
					send_data = reader.read(1024)
				reader.close()
			except FileNotFoundError:
				client.send("fail".encode())
		elif msg.startswith(b"upload"):
			receiveFile(msg, client)

""" =======================  Main    ========================== """
if __name__ == "__main__":
	socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socketServer.bind((host, port))
	socketServer.listen(20)
	print('The server is waiting... ')
	num = 0
	while True:
		num += 1
		client, address = socketServer.accept()
		t = Thread(target=handleClient, args=(client, address))
		t.start()
		print(str(num) + ' client is connected.')
	socketServer.close()