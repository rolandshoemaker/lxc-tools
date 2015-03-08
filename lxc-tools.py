import lxc
import os
from subprocess import Popen, call

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

def _run_command(args):
    cmd, cwd = args
    os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
    os.environ['HOME'] = '/root'
    return call(cmd, cwd=cwd)

def run_script(container, script, cwd="/", interpreter="bash"):
    rootfs = container.get_config_item("lxc.rootfs")
    if rootfs.startswith("overlayfs:"):
        raise ValueError("this doesn't work with overlay...")
    cmdpath = "%s/tmp/exec_script" % rootfs
    with open(cmdpath, "w+") as fd:
        fd.write(script)
    os.chmod(cmdpath, 0o755)
    cmd = [interpreter, "/tmp/exec_script"]

    print(" ==> Executing: \"%s\" in %s" % (" ".join(cmd), cwd))
    retval = container.attach_wait(_run_command,
                                   (cmd, cwd),
                                   env_policy=lxc.LXC_ATTACH_CLEAR_ENV)

    if retval != 0:
        raise ValueError("Failed to run the command.")

# ssh_cluster(get_running(), local_user="rolands")
run_script(get_running()[0], "ls")
