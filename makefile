# define the default target
.PHONY: run

# define the Python interpreter to use
PYTHON = python3.11

run: help

help:
	@echo "Usage:"
	@echo "  make run node <folder path> <server ip> - Run a Node"
	@echo "  make run tracker - Run the Tracker"

run-node:
	@$(PYTHON) -m src.FS_Node.main $(filter-out $@,$(MAKECMDGOALS))

run-tracker:
	@$(PYTHON) -m src.FS_Tracker.main

run-dns:
	@/usr/sbin/named -f -c /etc/bind/named.conf -u bind
