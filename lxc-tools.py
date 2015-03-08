import lxc
import os
from subprocess import Popen, call

def error(msg, exit_code=0):
    print("ERROR: %s" % (msg))
    exit(exit_code)

def get_running():
	return [c for c in lxc.list_containers(as_object=True) if c.state == "RUNNING"]

def get_stopped():
	return [c for c in lxc.list_containers(as_object=True) if c.state == "STOPPED"]

def stop(c, force=False):
	if not c.shutdown(30) and force:
		c.stop()
	return not c.running

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
       error("this doesn't work with overlay...")
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
        error("Failed to run the command.")

def rename(container, new_name, force_shutdown=False, restart=True):
    sed_rpl_cmd = ["sed", "-i", "'s/%s/%s/g'" % (container.name, new_name), "/etc/hostname"]]

    # before we do anything, make sure these isn't already a container duh
    if any([new_name == c.name for c in lxc.list_containers(as_object=True)]):
        eror("A container with this name already exists!")

    current_path = "%s/%s" % (container.get_config_path(), container.name)
    new_path = "%s/%s" % (container.get_config_path(), new_name)

    # set hostname
    if not container.running:
        if not start(container):
            error("couldn't start container %s" % (container.name))
    container.attach_wait(_run_command, (sed_rpl_cmd, "/"), env_policy=lxc.LXC_ATTACH_CLEAR_ENV)

    # shutdown container before moving
    if container.running:
        if not stop(container, force=force_shutdown):
            error("container %s is still running [force_shutdown: %s]" % (container.name, force_shutdown))

    # set config name
    container.set_config_item("lxc.rootfs", container.get_config_item("lxc.roofs").replace(container.name, new_name))
    container.set_config_item("lxc.mount", container.get_config_item("lxc.mount").replace(container.name, new_name))
    container.set_config_item("lxc.utsname", new_name)

    # move container to new home
    shutil.move(current_path, new_path)

    # restart container if ya want
    if restart:
        if not start(container):
            error("couldn't start container %s" % (container.name))

# ssh_cluster(get_running(), local_user="rolands")
# run_script(get_running()[0], "ls")
# get_running()[0].attach_wait(_run_command, (["ls"], "/"), env_policy=lxc.LXC_ATTACH_CLEAR_ENV)


