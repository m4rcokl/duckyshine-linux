#!/usr/bin/env python

import hid
import logging
import binascii

class DeviceNotFoundError(Exception):
  pass

class NotConnectedError(Exception):
  pass

class DuckyHID(object):
  """Class to communicate with Ducky Keyboard via hidapi"""

  def __init__(self):
    self._connected = False
    self._kbd = None
    pass


  def connect(self, vendorid=1241, productid=840, path=None):
    """Connect to Keyboard.
    If path is pecified, this overides the enumeration to find the device by
    vid and pid."""

    if path is None:
      path = self._find_device_path(vendorid, productid)
    
    self._kbd = hid.device()
    self._kbd.open_path(path)
    self._connected = True


  def _find_device_path(self, vid, pid):
    """Find the keyboard by enumerating hid devices looking for vid:pid,
    return path to second interface"""

    for d in hid.enumerate():
      if d["vendor_id"] == vid and d["product_id"] == pid:
        # found one interface of keyboard
        components = d["path"].decode("utf-8").split(":", 3)
        components[2] = "01" # always use second interface
        path = ":".join(components)
        return path.encode("utf-8")
    raise DeviceNotFoundError("No device with vid:pid of {}:{} found.".format(vid,pid))
    
  
  def send(self, data):
    """Send data to device, data should be 64 bytes"""
    if not self._connected:
      raise NotConnectedError("Cannot send data, not connected to any device.")
    logging.debug("-> {}".format(binascii.hexlify(data)))
    self._kbd.write(data)
    readData = self._kbd.read(64)
    readBytes = bytes(readData)
    logging.debug("<- {}".format(binascii.hexlify(readBytes)))
    return readBytes
 

  def close(self):
    """Close conection to device"""
    self._kbd.close()
    self._kbd = None
    self._connected = False


class Ducky(object):
  """Class to control colors of Ducky Keyboard
  Changing colors here should not be persistent.
  The Keyboard will reset to the previous mode, if the connection
  is closed."""
  
  INIT = binascii.unhexlify("41800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")

  EXIT = (
      binascii.unhexlify("51000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
      binascii.unhexlify("52000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"),
      binascii.unhexlify("41000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"))

  PREAMBLE = binascii.unhexlify("568100000100000008000000aaaaaaaa000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
  POSTAMBLE = binascii.unhexlify("51280000ff0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")

  USLayoutKeymap = {'esc': 20, '`': 23, 'tab': 26, 'caps': 29, 'lshift': 32, 'lctrl': 35, '1': 41, 'q': 44, 'a': 47, 'lwin': 53, 'f1': 56, '2': 59, 'w': 62, 's': 65, 'z': 68, 'lalt': 71, 'f2': 74, '3': 77, 'e': 80, 'd': 83, 'x': 86, 'f3': 92, '4': 95, 'r': 98, 'f': 101, 'c': 104, 'f4': 110, '5': 113, 't': 116, 'g': 119, 'v': 122, '6': 131, 'y': 134, 'h': 137, 'b': 140, 'space': 143, 'f5': 146, '7': 149, 'u': 152, 'j': 155, 'n': 158, 'f6': 164, '8': 167, 'i': 170, 'k': 173, 'm': 176, 'f7': 182, '9': 185, 'o': 188, 'l': 191, ',': 194, 'f8': 200, '0': 203, 'p': 206, ';': 209, '.': 212, 'ralt': 215, 'f9': 218, '-': 221, '[': 224, "'": 227, '/': 230, 'f10': 236, '=': 239, ']': 242, 'rwin': 251, 'f11': 254, 'rshift': 266, 'fn': 269, 'f12': 272, 'backspace': 275, '\\': 278, 'enter': 281, 'rctrl': 287, 'prtscr': 290, 'ins': 293, 'del': 296, 'left': 305, 'scrlk': 308, 'home': 311, 'end': 314, 'up': 320, 'down': 323, 'pause': 326, 'pgup': 329, 'pgdn': 332, 'right': 341, 'cal': 344, 'num': 347, 'num7': 350, 'num4': 353, 'num1': 356, 'num0': 359, 'mute': 362, 'num/': 365, 'num8': 368, 'num5': 371, 'num2': 374, 'vol-': 380, 'num*': 383, 'num9': 386, 'num6': 389, 'num3': 392, 'num.': 395, 'vol+': 398, 'num-': 401, 'num+': 404, 'numenter': 413}

  def __init__(self):
    self._kbd = None
    kbd = DuckyHID()
    kbd.connect()
    kbd.send(Ducky.INIT)
    self._kbd = kbd
    self._buf = self._newbuf()
    self._keyidx = Ducky.USLayoutKeymap
    self._overlay = {}
    self._basecolor = b"\x00\x00\x00"

  def _newbuf(self):
    """Return a default memory buffer with all leds off"""
    buf = [0] * 60 * 9
    buf[0:16] = [0x01,0x00,0x00,0x00,0x80,0x01,0x00,0xc1,0x00,0x00,0x00,0x00,0xff,0xff,0xff,0xff]
    return buf
  
  def __del__(self):
    self.disconnect()

  def disconnect(self):
    if not self._kbd is None:
      logging.info("Disconnecting gracefully...")
      for msg in Ducky.EXIT:
        self._kbd.send(msg)
      self._kbd.close()

  def setColorInBuf(self, idx, rgb):
    """Write a rgb triple to buf at idx"""
    if idx < 16 or idx > len(self._buf) - 3:
      raise IndexError("Must not access memory outside of range 16..buflen")
    if len(rgb) != 3:
      raise ValueError("RGB must contain a triple")
    self._buf[idx:idx+3] = rgb

  def commit(self):
    """Send updated colors to keyboard"""
    self._kbd.send(Ducky.PREAMBLE)
    header = [0x56, 0x83, 0x00, 0x00]
    for i in range(9):
      header [2] = i
      self._kbd.send(bytes(header + self._buf[i*60:i*60 + 60]))
    self._kbd.send(Ducky.POSTAMBLE)

  def off(self):
    self._buf = self._newbuf()

  def setKeyColor(self, keyname, color):
    """Change color of keyname to color.
    keyname must be from the list of keys in the layout.
    color must be a rgb triple."""
    idx = self._keyidx[keyname.lower()]
    self.setColorInBuf(idx, color)
    self._overlay[keyname.lower()] = color

  def removeKeyColor(self, keyname):
    """This will change the key back to base color"""
    key = keyname.lower()
    idx = self._keyidx[key]
    self.setColorInBuf(idx, self._basecolor)
    if key in self._overlay:
      del self._overlay[key]
    
  def setBaseColor(self, color):
    """Set background color.
    color must be a rgb triple."""
    self._basecolor = color
    for idx in self._keyidx.values():
      self.setColorInBuf(idx, color)
    # need to fix keys from overlay
    for key, color in self._overlay.items():
      idx = self._keyidx[key]
      self.setColorInBuf(idx, color)
      
  def clearAllKeys(self):
    """Set all keys back to base color"""
    self._overlay = {}
    self.setBaseColor(self._basecolor)

