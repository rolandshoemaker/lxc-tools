#!/usr/bin/python3

import lxc
import os
import sys
import ipaddress
import pprint
import subprocess
import time

def is_valid_ipv4(ip):
	try:
		ipaddress.ip_address(ip)
		return True
	except ValueError:
		return False

def write_bind(container, aRecord, reverseRecord):
	if container:
		rootfs = container.get_config_item("lxc.rootfs")
		bindpath = "%s/etc/bind/" % rootfs
		if aRecord:
			with open(bindpath+"db."+dnsdomain, "a") as fd:
				fd.write(aRecord)
		if reverseRecord:
			with open(bindpath+"db."+reversedomain, "a") as fd:
				fd.write(reverseRecord)

def execute(container, cmd, cwd="/"):
    def run_command(args):
        cmd, cwd = args

        os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
        os.environ['HOME'] = '/root'

        return subprocess.call(cmd, cwd=cwd)

    if isinstance(cmd, str):
        rootfs = container.get_config_item("lxc.rootfs")
        cmdpath = "%s/tmp/exec_script" % rootfs
        with open(cmdpath, "w+") as fd:
            fd.write(cmd)
        os.chmod(cmdpath, 0o755)
        cmd = ["/tmp/exec_script"]

    print(" ==> Executing: \"%s\" in %s" % (" ".join(cmd), cwd))
    retval = container.attach_wait(run_command,
                                   (cmd, cwd),
                                   env_policy=lxc.LXC_ATTACH_CLEAR_ENV)

    if retval != 0:
        raise Error("Failed to run the command.")

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

dnsdomain = "home.local"
reversedomain = "192"
baseIp = "192.168.1.190"
dnsContainer = "haku-lxc"
baseName = "base-lxc"
netmask = "255.255.255.0"
base = lxc.Container(baseName)

if not os.geteuid() == 0:
	print(colors.WARNING+baseName+" is a privileged container."+colors.ENDC)
	sys.exit(1)
print(colors.OKGREEN+"Starting base image"+colors.ENDC)
base.start()
print(colors.OKGREEN+"Waiting for network to come up"+colors.ENDC)
time.sleep(10)
print(colors.OKGREEN+"Updating base container packages..."+colors.ENDC)
base.attach_wait(lxc.attach_run_command, ["apt-get", "update"])
base.attach_wait(lxc.attach_run_command, ["apt-get", "dist-upgrade", "-y"])
base.attach_wait(lxc.attach_run_command, ["apt-get", "upgrade", "-y"])
if not base.shutdown(30):
	base.stop()

hostname = input("[new container name]# ")
clone = lxc.Container(hostname)

if clone.defined:
	print(colors.WARNING+"The container name: "+hostname+", is already in use."+colors.ENDC)
	sys.exit(1)

print(colors.OKGREEN+"Cloning "+baseName+" to "+hostname+"..."+colors.ENDC)
clone = base.clone(hostname, flags=lxc.LXC_CLONE_SNAPSHOT)
print(colors.OKGREEN+"Starting "+hostname+"..."+colors.ENDC)
clone.start()

while True:
	ip = input("[ip for "+hostname+"]# ")
	if is_valid_ipv4(ip):
		break
	else:
		print(colors.WARNING+ip+" is not a valid ipv4 address!"+colors.ENDC)

if not type(ip) == 'undefined':
	print(colors.OKGREEN+"Setting "+hostname+"s IP to "+ip+colors.ENDC)

	execute(clone, ["sed", "-i.bak", "-e", "s/192.168.1.190/"+ip+"/g", "/etc/network/interfaces"])

	if not clone.shutdown(30):
		clone.stop()
	clone.start()	

while True:
	bind = input("[add records to bind server? Y/n]# ")
	if bind in ['y', 'n', 'Y', 'N', '']:
                break
	else:
                print(colors.WARNING+"Either y or n"+colors.ENDC)

if bind == 'Y' or bind == 'y' or bind == '':
	dnsd = lxc.Container(dnsContainer)
	octet = ip.split('.')

	print(colors.OKGREEN+"Adding DNS records to "+dnsContainer+" for "+hostname+colors.ENDC)

	aRecord = hostname+"\t\tIN\tA\t"+ip
	reverseRecord = octet[3]+"\tIN\tPTR\t"+hostname+"."+dnsdomain+"."
	write_bind(dnsd, aRecord, reverseRecord)

	print(colors.OKGREEN+"Restarting bind9..."+colors.ENDC)

	dnsd.attach_wait(lxc.attach_run_command, ["service", "bind9", "restart"])

while True:
	question = input("[leave running? Y/n (C to drop into a shell on "+hostname+")]# ")
	if question in ['y', 'n', 'Y', 'N', 'C', '']:
		break
	else:
		print(colors.WARNING+"Either y, n, or C"+colors.ENDC)

if question == 'n' or question == 'N':
	print(colors.OKGREEN+"Shutting down "+hostname+"..."+colors.ENDC)
	if not clone.shutdown(30):
		clone.stop()

if question == 'C':
	print(colors.OKGREEN+"Down the rabbit hole..."+colors.ENDC)
	os.system("lxc-attach -n "+hostname)
