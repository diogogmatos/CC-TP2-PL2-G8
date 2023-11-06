# Define the default target
.PHONY: run

# Define the Python interpreter to use
PYTHON = python

# Targets and recipes
run: help

help:
	@echo "Usage:"
	@echo "  make run node <folder path> <server ip> - Run a Node"
	@echo "  make run tracker - Run the Tracker"

run-node:
	@$(PYTHON) -m src.FS_Node.main $(filter-out $@,$(MAKECMDGOALS))

run-tracker:
	@$(PYTHON) -m src.FS_Tracker.main
