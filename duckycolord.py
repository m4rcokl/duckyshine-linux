#!/usr/bin/env python

import os
import pwd
import grp
import zmq
import json
import logging
import argparse
import duckyshine

COLORD_SOCKET = "/tmp/duckycolord"


parser = argparse.ArgumentParser("Ducky Shine Color Daemon")
parser.add_argument("-u", "--user", help="Change owner of socket to his user")
parser.add_argument("-g", "--group", help="Change group of socket to his group")
parser.add_argument("-b", "--basecolor", default="0,0,0", help="Set r,g,b base color of keyboard")

def setBaseColor(kbd, col):
  try:
    r,g,b = [int(x) for x in col.split(",")]
    for c in r,g,b:
      if c < 0 or c > 255:
        log.error("Color cannot be out of range 0..255")
        sys.exit(1)
    basecolor = (r,g,b)
  except ValueError:
    log.error("Color must be specified as r,g,b where r, g and b are in 0..255")
    sys.exit(1)
  kbd.setBaseColor(basecolor)
  kbd.commit()



if __name__ == "__main__":
  args = parser.parse_args()

  logging.info("Opening Ducky Shine 7...")
  kbd = duckyshine.Ducky()
  logging.info("opened.")
  
  setBaseColor(kbd, args.basecolor)

  # open socket and adjust ownership
  context = zmq.Context()
  socket = context.socket(zmq.PULL)
  socket.bind("ipc://{}".format(COLORD_SOCKET))
  uid = -1
  gid = -1
  if args.user:
    uid = pwd.getpwnam(args.user).pw_uid
  if args.group:
    gid = grp.getgrnam(args.group).gr_gid
  if uid != -1 or gid != -1:
    os.chown(COLORD_SOCKET, uid, gid) 
  os.chmod(COLORD_SOCKET, 0o660)


  while True:
    msg = socket.recv()
    print(msg)
    try:
      keys = json.loads(msg)
      logging.debug(keys)
    except ValueError as e:
      log.warning("Could not decode JSON: {}".format(e))
      continue
    # set base color first, before handling individual keys
    if "basecolor" in keys:
      kbd.setBaseColor(keys["basecolor"])

    for key, color in keys.items():
      if key == "basecolor":
        continue
      try:
        if not color:
          kbd.removeKeyColor(key)
        else:
          kbd.setKeyColor(key, color)
      except KeyError:
        log.warning("Unknown key: {}".format(key))
        continue
      except ValueError:
        log.warning("Color not recognized: {}".format(color))
        continue
    kbd.commit()

  logging.info("closing...")
