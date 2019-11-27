# Linux Ducky Shine Color Control

This is a python lib intended to control the color of Ducky Shine keyboards. Developed and tested with a Shine 7.
It's losely based on https://github.com/Latedi/DuckyAPI .
Further reverse engineering of the protocol allowed a significant reduction of necessary USB messages.

*WARNING*
The protocol has been reverse engineered and therefor is not fully understood. So it might break or crash the keyboard. You have been warned. Use this on your own risk.

The module is in the subdirectory duckyshine.
Inlcuded are also a few sample applications.

## demo_random.py

Uses the module to assign some random colors to random keys over time.

## duckycolord.py

This is a daemon, which is listening on a zeromq socket waiting for requests from other applications to set key colors. It uses the module directly to set colors.
If you do not want change ownership of all hidraw devices for the keyboard (this might pose a risk for sniffing keystrokes from other sessions), this daemon supports running as root and changing access rights for the socket, so userspace applications only can change colors.

### red_alert.py

Talks to the ducky color daemon and blinks the keyboard red.

### all_green.py

Talks to the daemon and switches the keyboard back to green.
