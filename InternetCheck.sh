#!/bin/bash
# Variables de entorno
ENV_DIR="/home/villafapd/Documents/PythonProjects/InternetCheck/.venv"
lxterminal --title="Internet Checker" --geometry=60x30+10+10 --command="/bin/bash -c 'source $ENV_DIR/bin/activate; exec python3.11 /home/villafapd/Documents/PythonProjects/InternetCheck/main.py'"