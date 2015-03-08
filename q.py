import subprocess
import lxc
import os, sys

SCRIPT = """
#!/bin/bash
KEYTT=""

if [ -d "=p" ]; then
   rm -rf "=p"
fi

if [ ! -d /root/.ssh ]; then
   mkdir /root/.ssh
fi
if [ -e /root/.ssh/authorized_keys ]; then
    rm -f /root/.ssh/authorized_keys
fi
touch /root/.ssh/authorized_keys
echo "$KEYTT" >/root/.ssh/authorized_keys
"""



def execute(container, cmd, cwd="/"):
    def run_command(args):
        cmd, cwd = args

        os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
        os.environ['HOME'] = '/root'

        return subprocess.call(cmd, cwd=cwd)

    if isinstance(cmd, str):
        print("yup")
        rootfs = container.get_config_item("lxc.rootfs")
        if rootfs.startswith("overlayfs:"):
            rootfs = rootfs.split("rootfs:")[-1]
        cmdpath = "%s/tmp/exec_script" % rootfs
        with open(cmdpath, "w+") as fd:
            fd.write(cmd)
        os.chmod(cmdpath, 0o755)
        cmd = ["bash", "/tmp/exec_script"]

    print(" ==> Executing: \"%s\" in %s" % (" ".join(cmd), cwd))
    retval = container.attach_wait(run_command,
                                   (cmd, cwd),
                                   env_policy=lxc.LXC_ATTACH_CLEAR_ENV)

    if retval != 0:
        raise ValueError("Failed to run the command.")

for container in lxc.list_containers(as_object=True):
        started = False
        stopped = bool()
        if not container.running:
                stopped = True
                if not container.start():
                        continue
                started=True
        if not container.state == "RUNNING":
                continue
        if not container.get_ips(timeout=30):
                continue

        print(container.name)
        execute(container, SCRIPT)

        if started and (stopped):
                if not container.shutdown(30):
                        container.stop()

