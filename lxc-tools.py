import lxc
from subprocess import Popen

def get_running():
	return [c for c in lxc.list_containers(as_object=True) if c.state == "RUNNING"]

def get_stopped():
	return [c for c in lxc.list_containers(as_object=True) if c.state == "STOPPED"]

def stop(c):
	if not c.shutdown(30):
		c.stop()
		return False
	return True

def start(c):
	if c.running:
		print("%s already started" % (c.name))
		return True

	if not c.start():
		print("couldn't start %s" % (c.name))
		return False

	return True

def stop_all(cs):
	return [start(c) for c in cs]

def start_all(cs):
	return [stop(c) for c in cs]

def ssh_cluster(cs, user="root", local_user=None):
	tcmd = ["tm", "ms"]
	if local_user:
		tcmd = ["sudo", "-u", local_user]+tcmd
	ssh = Popen(tcmd+["%s@%s" % (user, c.name) for c in cs])
	ssh.wait()

ssh_cluster(get_running(), local_user="rolands")
