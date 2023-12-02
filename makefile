# define the default target
.PHONY: run

# define the Python interpreter to use
PYTHON = python3.11

ZONES = \
	'zone "1.1.10.in-addr.arpa" {\n    type master;\n    file "/etc/bind/example.10.1.1";\n};' \
	'zone "2.2.10.in-addr.arpa" {\n    type master;\n    file "/etc/bind/example.10.2.2";\n};' \
	'zone "3.3.10.in-addr.arpa" {\n    type master;\n    file "/etc/bind/example.10.3.3";\n};' \
	'zone "4.4.10.in-addr.arpa" {\n    type master;\n    file "/etc/bind/example.10.4.4";\n};'

APPEND = 'zone "local" {\n	type master;\n	file "/etc/bind/zones/example.zone";\n};'

config:
	sudo sh assets/installbind9.sh
	sudo mkdir /etc/bind/zones
	sudo cp assets/example.zone /etc/bind/zones/example.zone
	sudo echo -e $(APPEND) >> /etc/bind/named.conf.default-zones
	sudo cp /etc/bind/named.conf.default-zones.backup /etc/bind/named.conf.default-zones
	sudo echo -e $(ZONES) >> /etc/bind/named.conf.default-zones
	sudo cp assets/example10.1.1.txt /etc/bind/zones/
	sudo cp assets/example10.2.2.txt /etc/bind/zones/
	sudo cp assets/example10.3.3.txt /etc/bind/zones/
	sudo cp assets/example10.4.4.txt /etc/bind/zones/

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
