lxc-tools
=========

a collection of tools to help manage lxc containers

- lxc-clone-base.py - Intended to allow you to quickly clone a new container from a base container (this container doesn't need to be left running and be updated using a cron-job, although this script will start it, check for apt updates and install them then stop it befor cloning), update it's network interface, and optionally add dns records to another container that is running bind9. (Need to add autostart question as well...) This script uses privileged containers so you must be root or sudo to run it.

I plan on adding a few more tools namely:
- lxc-backup-base.py - create a rotating backup of the base image config file as well as dpkg -l
- lxc-build-base.py - create a base from scratch or restore a base from backup config file and dpkg list
