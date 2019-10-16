# -*- coding: utf-8 -*-
"""
File:   Project01.py
Author:  Zhewei Song
Date: 10th Oct 2019
Desc: Hello, this is client program.

"""
""" =======================  Import dependencies ========================== """
import socket
import sys


"""================================== Usage ==================================="""
usage = """

Please use the dir, upload and get instruction: 
upload: upload filename
get : get filename

"""
hp = input('Please type the host address and port number: ')
host = hp[1: 10]
port = int(hp[11: 15])

""" =======================  Receive File function ========================== """
def receiveFile(command, s):
	fileName = command.split(" ")[1]
	s.sendall("|$|".join(command.split(" ")).encode())
	recv_data = s.recv(1024)
	if recv_data.startswith(b"success"):
		filesize = int(recv_data.split(b"|$|")[0][7:])
		writer = open(fileName, "wb")
		writer.write(recv_data[10+len(str(filesize)):])
		rest_size = filesize - 1024 + 10 + len(str(filesize))
		if rest_size < 0:
			pass
		else:
			if rest_size >= 1024:
				recv_data = s.recv(1024)
				rest_size -= 1024
			elif rest_size > 0:
				recv_data = s.recv(rest_size)
				rest_size = 0
			while rest_size>0:
				writer.write(recv_data)
				if rest_size >= 1024:
					recv_data = s.recv(1024)
					rest_size -= 1024
				else:
					recv_data = s.recv(rest_size)
					rest_size = 0
			writer.write(recv_data)
		writer.close()
		print("Received ", fileName)
	else:
		print(fileName, "does not exist!")

""" =======================  Upload file function ========================== """
def uploadFile(command, s):
	try:
		file = command.split(" ")[1]
		reader = open(file, 'rb')

		with open(file, 'rb') as f:
			filesize = len(f.read())
		header = "|$|".join(["upload", file, str(filesize)]) + "|$|"
		send_data = reader.read(1024 - len(header))
		s.sendall(header.encode() + send_data)
		send_data = reader.read(1024)
		while send_data:
			s.sendall(send_data)
			send_data = reader.read(1024)
	except FileNotFoundError:
		print("File you asked does not exist!")


""" =======================  Main  ========================== """
if __name__ == "__main__":
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))
	isLoggedIn = False
	while True:
		while not isLoggedIn:
			username = input("Please enter the username: ")
			password = input("Please enter the password: ")
			s.sendall("|$|".join(["login", username, password]).encode())
			login_info = s.recv(1024).decode()
			print(login_info)
			if "success" in login_info:
				isLoggedIn = True
			else:
				print("Username or password error!")
		command = input(usage)
		if command.startswith("dir"):
			s.sendall("dir".encode())
			for file in s.recv(1024).decode().split(" "):
				print(file)
		elif command.startswith("get"):
			receiveFile(command, s)
		elif command.startswith("upload"):
			uploadFile(command, s)
	s.close()