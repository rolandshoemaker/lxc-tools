import subprocess
import lxc
import os, sys

SCRIPT = """
#!/bin/bash
KEYTT="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGNsr1tbqH4BSGql1VNzSA9ZVi4Fp5LsUtFdQf3DoNL+e5OA/AU+tW1DBu28iYhdwmLn34yfFs7NdbbbDYH9CwIVOaegBcmx7z8C/YO+NsoORL3bCB2NJZa9LO/v+CsULOArklpme21v+HJbG/uiF5cKAm8Nj7kMh1D/zTW6BkUWbUxkD2wNsFUGgjjCmjnRF2ED5YJPmjt4EZaqIXpgNsj6AjYHQPY6i09O8iG5ntekLOjoZ5s24lEq2gUMl6qc1EaHDIXVOHtohw5hdSWJvHbonXUC5Yfuq6+ZSZHI79PXheUfekNW1xEAmMbsxLC4jW39Ze1gFfPaCRRQPfTMS1 rolands@kamaji"

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

