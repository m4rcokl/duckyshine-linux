#!/usr/bin/env python

import sys
import time
import random
import duckyshine

print("Opening Ducky Shine 7...")
kbd = duckyshine.Ducky()
print("opened.")

keys = list(kbd._keyidx.items())

while True:
  r = random.randint(0,len(keys)-1)
  key, idx = keys[r]
  color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
  kbd.setKeyColor(key, color)
  kbd.commit()
  print("{} -> {c[0]},{c[1]},{c[2]}".format(key,c=color))
  time.sleep(0.1)

print("closing...")
