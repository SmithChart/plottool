#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from hpgl import HPGL
try:
	import serial
except:
	print("You need to install pyserial. "
		"On Debian/Ubuntu try "
		"sudo apt-get install python-serial")
	exit(1)

# make input python2 and python3 compatible
try:
	input = raw_input
except NameError:
	pass

parser = argparse.ArgumentParser(description="Process all arguments ")
parser.add_argument("-p", "--port", metavar="PORT", type=str, help="Serial port (default: /dev/ttyUSB0)", default="/dev/ttyUSB0")
parser.add_argument("-m", "--magic", action="store_true", help="Enable auto-optimize")
parser.add_argument("-w", "--width", metavar="WIDTH", type=int, help="Scale to width in mm")
parser.add_argument("--pen", action="store_true", help="Disable cut optimization for rotating knifes")
parser.add_argument("file", type=str, help="the HPGL-file you want to plot")
args = parser.parse_args()

if not os.path.exists(args.port):
	print("The port {} does not exist.".format(args.port))
	exit(1)

print("Using port: {}".format(args.port))
try:
	HPGLinput = HPGL(args.file)
except:
	print("no/wrong/empty file given in argument.")
	exit(128)


# do optimize stuff:
blade_optimize = False
optimize = False
reroute = False
margin = 5

if args.magic:
	blade_optimize = True
	reroute = True
	optimize = True

if args.width is not None:
	HPGLinput.scaleToWidth(args.width)

if args.pen:
	blade_optimize = False

if optimize:
	HPGLinput.optimize()
	HPGLinput.fit()

if blade_optimize:
	HPGLinput.optimizeCut(0.25)
	HPGLinput.bladeOffset(0.25)

if reroute:
	HPGLinput.rerouteXY()


print("Plotting file: " + args.file)
w, h = HPGLinput.getSize()
print("Plotting area is {width:.1f}cm x {height:.1f}cm".format(width=w / 10, height=h / 10))
print(" -> Total area:     {area:.1f} cm^2".format(area=w / 10 * h / 10))
movement = sum(HPGLinput.getLength())
print(" -> Total movement: {:.1f} cm".format(movement / 10))

try:
	cont = input("continue? (y/n) ")
except KeyboardInterrupt:
	exit(0)
if cont != "y":
	exit(0)

HPGLdata = HPGLinput.getHPGL()
print("{} characters loaded".format(len(HPGLdata)))

port = serial.Serial(
	port=args.port,
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	rtscts=True,
	dsrdtr=True
)

splitted = HPGLdata.split(";")
total = len(splitted)

sys.stdout.write("starting...")
port.write(";IN;")

for i, command in enumerate(splitted):
	sys.stdout.write("\rsending... {percent:.1f}% done ({done}/{total})".format(percent=(i + 1) * 100.0 / total, done=i + 1, total=total))
	sys.stdout.flush()
	# ignore empty
	if not command:
		continue
	port.write(command + ";")

port.write("@;")
sys.stdout.write("\n")

__author__ = "doommaster"
