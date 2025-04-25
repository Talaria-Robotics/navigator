#!/bin/sh
sudo pigpiod
sudo venv/bin/python -m sanic server:app --port 8075 --host ::
