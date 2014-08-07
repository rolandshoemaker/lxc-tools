#!/usr/bin/python3

import lxc
import os
import sys
import ipaddress

def is_valid_ipv4(ip):
	try:
		ipaddress.ip_address(ip)
		return True
	except ValueError:
		return False

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

dnsdomain = "home.local"
baseIp = "192.168.1.190"
dnsContainer = "haku-lxc"
baseName = "base-lxc"
base = lxc.Container(baseName)

if not os.geteuid() == 0:
	print(colors.WARNING+baseName+" is a privileged container."+colors.ENDC)
	sys.exit(1)

print(colors.OKGREEN+"Updating base container..."+colors.ENDC)
base.start()
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
	clone.attach_wait(lxc.attach_run_command, ["ifconfig", "eth0", ip, "netmask", netmask, "up"])
	clone.attach_wait(lxc.attach_run_command, ["sed", "-i.bak", "s/"+baseIp+"/"+ip+"/g", "/etc/network/interfaces", "&&", "rm", "interfaces.bak"])
	clone.attach_wait(lxc.attach_run_command, ["ifdown", "eth0", "&&", "ifup", "eth0"])

while True:
	bind = input("[add records to bind server? Y/n]# ")
	if bind n in ['y', 'n', 'Y', 'N', '']:
                break
        else:
                print(colors.WARNING+"Either y or n"+colors.ENDC)

if bind == 'Y' or bind == 'y' or bind == '':
	dnsd = lxc.Container(dnsContainer)
	octet = ip.split('.')
	print(colors.OKGREEN+"Adding DNS records to "+dnsContainer+" for "+hostname+colors.ENDC)
	dnsd.attach_wait(lxc.attach_run_command, ["echo", hostname, "IN", "A", ip, ">>", "/etc/bind/db."+dnsdomain])
	dnsd.attach_wait(lxc.attach_run_command, ["echo", octet[3], "IN", "PTR", hostname+dnsdomain+".", ">>", "/etc/bind/db.192"])
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
