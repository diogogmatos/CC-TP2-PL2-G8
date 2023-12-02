# define the default target
.PHONY: run

# define the Python interpreter to use
PYTHON = python3.11

ZONES = \
	'zone "1.1.10.in-addr.arpa" {\n    type master;\n    file "/etc/bind/example.10.1.1";\n};' \
	'zone "2.2.10.in-addr.arpa" {\n    type master;\n    file "/etc/bind/example.10.2.2";\n};' \
	'zone "3.3.10.in-addr.arpa" {\n    type master;\n    file "/etc/bind/example.10.3.3";\n};' \
	'zone "4.4.10.in-addr.arpa" {\n    type master;\n    file "/etc/bind/example.10.4.4";\n};'

/etc/bind/named.conf.default-zones: /etc/bind/named.conf.default-zones.backup
	@cp /etc/bind/named.conf.default-zones.backup /etc/bind/named.conf.default-zones
	@echo -e $(ZONES) >> /etc/bind/named.conf.default-zones

/etc/bind/zones/example.10.1.1: example10.1.1.txt
    @cp dns/example10.1.1.txt /etc/bind/zones/

/etc/bind/zones/example.10.2.2: example10.2.2.txt
    @cp dns/example10.2.2.txt /etc/bind/zones/

/etc/bind/zones/example.10.3.3: example10.3.3.txt
    @cp dns/example10.3.3.txt /etc/bind/zones/

/etc/bind/zones/example.10.4.4: example10.4.4.txt
    @cp dns/example10.4.4.txt /etc/bind/zones/

config: /etc/bind/named.conf.default-zones
	mkdir -p /etc/bind/zones
	/etc/bind/zones/example.10.1.1 \
	/etc/bind/zones/example.10.2.2 \
	/etc/bind/zones/example.10.3.3 \
	/etc/bind/zones/example.10.4.4

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
