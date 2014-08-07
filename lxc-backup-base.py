#!/usr/bin/python3

import lxc
import os
import sys
import subprocess
import socket
import random
import time
import datetime
import re
import shutil

import pprint

def get_dpkg_list(host, port):
	print("		["+baseName+"] Generating dpkg list")
	proc = subprocess.Popen("dpkg-query -W -f '${status} ${package}\n' | sed -n 's/^install ok installed //p'", stdout=subprocess.PIPE, shell=True)

	print("		["+baseName+"] Opening socket")
	send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	print("		["+baseName+"] Connecting to "+host+":"+str(port))
	send.connect((host, port))

	print("		["+baseName+"] Sending list")
	try:
		send.sendall(proc.stdout.read())
	except socket.error:
		print("Send failed")

if not os.geteuid() == 0:
        print(baseName+" is a privileged container.")
        sys.exit(1)

baseName = "base-lxc"
backupRoot = "/root/lxc-backups/"
day = datetime.datetime.today().weekday()
backupFolder = backupRoot+str(day)+"."+baseName+"/"
base = lxc.Container(baseName)
baseConfig = base.get_config_path()+"/"+baseName+"/config"

if not os.path.exists(backupFolder):
	print("Building directory structure")
	for i in range(0, 7):
		if not os.path.exists(backupRoot+str(i)+"."+baseName+"/"):
			os.makedirs(backupRoot+str(i)+"."+baseName+"/")

print("Starting "+baseName)
base.start()

print("Grabbing dpkg installed list")
recieve = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
	try:
		hostPort = random.randrange(5000,8000)
		recieve.bind((socket.gethostname(), hostPort))
		break
	except socket.error:
		print("Bind failed: ")

host = socket.gethostname()
print("	Opened socket on "+host+":"+str(hostPort))

recieve.listen(1)

print("	Listening for dpkg list from "+baseName)
while 1:
	print("	Sending dpkg python to "+baseName)
	try:
		base.attach(get_dpkg_list(host, hostPort))
	except:
		pass
	conn, addr = recieve.accept()
	data = conn.recv(4096)
	if data:
		print("	Recieved list")
		break

dpkgList = str(data).split("\\n")
print("Writing dpkg list to "+backupFolder+"dpkg")
try:
	os.remove(backupFolder+"dpkg")
except OSError:
	pass
with open(backupFolder+"dpkg", "w+") as file:
	for package in dpkgList:
		package = re.sub('b*\'', '', package)
		file.write("%s\n" % package)

conn.close()
recieve.close()

if not base.shutdown(30):
        base.stop()

# snapshot of container
print("Creating snapshot of "+baseName)
snapshotName = str(day)+"."+baseName
if lxc.Container(snapshotName):
	destroyme = lxc.Container(snapshotName)
	destroyme.destroy()
baseBackup = base.clone(snapshotName, flags=lxc.LXC_CLONE_SNAPSHOT)
snaps = baseBackup.snapshot_list()

if snapshotName in snaps:
	baseBackup.snapshot_destroy(snapshotName)

baseBackup.snapshot(snapshotName)
baseBackup.destroy()

print("Soft-linking snapshot to "+backupFolder+"snap/")
try:
	os.remove(backupFolder+"snap")
except OSError:
	pass
os.symlink("/var/lib/lxcsnaps/"+snapshotName+"/snap0", backupFolder+"snap")
