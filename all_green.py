#!/usr/bin/env python3
import time
import zmq
import json

COLORDSOCK = "/tmp/duckycolord"

ctx = zmq.Context()
socket = ctx.socket(zmq.PUSH)
socket.connect("ipc://{}".format(COLORDSOCK))

msg = {"basecolor": [0x00, 0xaa, 0x00]}
socket.send(json.dumps(msg).encode("utf-8"))

socket.close()

