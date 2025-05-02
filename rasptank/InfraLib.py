#!/usr/bin/env python3
# Python IR transmitter
# Requires pigpio library
# Supports NEC, RC-5 and raw IR.
# Danijel Tudek, Aug 2016

import ctypes
import time
import RPi.GPIO as GPIO
import threading
from datetime import datetime
import multiprocessing
import math
from functools import reduce
import uuid


#####################################
#             IR Blaster            #
#####################################

# This is the struct required by pigpio library.
# We store the individual pulses and their duration here. (In an array of these structs.)
class Pulses_struct(ctypes.Structure):
	_fields_ = [("gpioOn", ctypes.c_uint32),
				("gpioOff", ctypes.c_uint32),
				("usDelay", ctypes.c_uint32)]

# Since both NEC and RC-5 protocols use the same method for generating waveform,
# it can be put in a separate class and called from both protocol's classes.
class Wave_generator():
	def __init__(self,protocol):
		self.protocol = protocol
		MAX_PULSES = 12000 # from pigpio.h
		Pulses_array = Pulses_struct * MAX_PULSES
		self.pulses = Pulses_array()
		self.pulse_count = 0

	def add_pulse(self, gpioOn, gpioOff, usDelay):
		self.pulses[self.pulse_count].gpioOn = gpioOn
		self.pulses[self.pulse_count].gpioOff = gpioOff
		self.pulses[self.pulse_count].usDelay = usDelay
		self.pulse_count += 1

	# Pull the specified output pin low
	def zero(self, duration):
		self.add_pulse(0, 1 << self.protocol.master.gpio_pin, duration)

	# Protocol-agnostic square wave generator
	def one(self, duration):
		period_time = 1000000.0 / self.protocol.frequency
		on_duration = int(round(period_time * self.protocol.duty_cycle))
		off_duration = int(round(period_time * (1.0 - self.protocol.duty_cycle)))
		total_periods = int(round(duration/period_time))
		total_pulses = total_periods * 2

		# Generate square wave on the specified output pin
		for i in range(total_pulses):
			if i % 2 == 0:
				self.add_pulse(1 << self.protocol.master.gpio_pin, 0, on_duration)
			else:
				self.add_pulse(0, 1 << self.protocol.master.gpio_pin, off_duration)

# NEC protocol class
class NEC():
	def __init__(self,
				master,
				frequency=38000,
				duty_cycle=0.33,
				leading_pulse_duration=9000,
				leading_gap_duration=4500,
				one_pulse_duration = 562,
				one_gap_duration = 1686,
				zero_pulse_duration = 562,
				zero_gap_duration = 562,
				trailing_pulse = 0,
				verbose = False):
		self.master = master
		self.wave_generator = Wave_generator(self)
		self.frequency = frequency # in Hz, 38000 per specification
		self.duty_cycle = duty_cycle # duty cycle of high state pulse
		# Durations of high pulse and low "gap".
		# The NEC protocol defines pulse and gap lengths, but we can never expect
		# that any given TV will follow the protocol specification.
		self.leading_pulse_duration = leading_pulse_duration # in microseconds, 9000 per specification
		self.leading_gap_duration = leading_gap_duration # in microseconds, 4500 per specification
		self.one_pulse_duration = one_pulse_duration # in microseconds, 562 per specification
		self.one_gap_duration = one_gap_duration # in microseconds, 1686 per specification
		self.zero_pulse_duration = zero_pulse_duration # in microseconds, 562 per specification
		self.zero_gap_duration = zero_gap_duration # in microseconds, 562 per specification
		self.trailing_pulse = trailing_pulse # trailing 562 microseconds pulse, some remotes send it, some don't
		self.verbose = verbose
		if self.verbose:
			("NEC protocol initialized")

	# Send AGC burst before transmission
	def send_agc(self):
		if self.verbose:
			print("Sending AGC burst")
		self.wave_generator.one(self.leading_pulse_duration)
		self.wave_generator.zero(self.leading_gap_duration)

	# Trailing pulse is just a burst with the duration of standard pulse.
	def send_trailing_pulse(self):
		if self.verbose:
			print("Sending trailing pulse")
		self.wave_generator.one(self.one_pulse_duration)

	# This function is processing IR code. Leaves room for possible manipulation
	# of the code before processing it.
	def process_code(self, ircode):
		if (self.leading_pulse_duration > 0) or (self.leading_gap_duration > 0):
			self.send_agc()
		for i in ircode:
			if i == "0":
				self.zero()
			elif i == "1":
				self.one()
			else:
				if self.verbose:
					print("ERROR! Non-binary digit!")
				return 1
		if self.trailing_pulse == 1:
			self.send_trailing_pulse()
		return 0

	# Generate zero or one in NEC protocol
	# Zero is represented by a pulse and a gap of the same length
	def zero(self):
		self.wave_generator.one(self.zero_pulse_duration)
		self.wave_generator.zero(self.zero_gap_duration)

	# One is represented by a pulse and a gap three times longer than the pulse
	def one(self):
		self.wave_generator.one(self.one_pulse_duration)
		self.wave_generator.zero(self.one_gap_duration)


class IR():
	def __init__(self, gpio_pin, protocol, protocol_config, verbose=False):
		self.verbose = verbose
		if self.verbose:
			print("Starting IR")
			print("Loading libpigpio.so")
		self.pigpio = ctypes.CDLL('libpigpio.so')
		if self.verbose:
			print("Initializing pigpio")
		self.pigpio.gpioInitialise()
		PI_OUTPUT = 1 # from pigpio.h
		self.gpio_pin = gpio_pin
		if self.verbose:
			print("Configuring pin %d as output" % self.gpio_pin)
		self.pigpio.gpioSetMode(self.gpio_pin, PI_OUTPUT) # pin 17 is used in LIRC by default
		if self.verbose:
			print("Initializing protocol")
		if protocol == "NEC":
			self.protocol = NEC(self, **protocol_config)
		else:
			if self.verbose:
				print("Protocol not specified! Exiting...")
			return 1
		if self.verbose:
			print("IR ready")

	# send_code takes care of sending the processed IR code to pigpio.
	# IR code itself is processed and converted to pigpio structs by protocol's classes.
	def send_code(self, ircode):
		if self.verbose:
			print("Processing IR code: %s" % ircode)
		code = self.protocol.process_code(ircode)
		if code != 0:
			if self.verbose:
				print("Error in processing IR code!")
			return 1
		clear = self.pigpio.gpioWaveClear()
		if clear != 0:
			if self.verbose:
				print("Error in clearing wave!")
			return 1
		pulses = self.pigpio.gpioWaveAddGeneric(self.protocol.wave_generator.pulse_count, self.protocol.wave_generator.pulses)
		if pulses < 0:
			if self.verbose:
				print("Error in adding wave!")
			return 1
		wave_id = self.pigpio.gpioWaveCreate()
		# Unlike the C implementation, in Python the wave_id seems to always be 0.
		if wave_id >= 0:
			if self.verbose:
				print("Sending wave...")
			result = self.pigpio.gpioWaveTxSend(wave_id, 0)
			if result >= 0:
				if self.verbose:
					print("Success! (result: %d)" % result)
			else:
				if self.verbose:
					print("Error! (result: %d)" % result)
				return 1
		else:
			if self.verbose:
				print("Error creating wave: %d" % wave_id)
			return 1
		while self.pigpio.gpioWaveTxBusy():
			time.sleep(0.1)
		if self.verbose:
			print("Deleting wave")
		self.pigpio.gpioWaveDelete(wave_id)
		if self.verbose:
			print("Terminating pigpio")
		self.pigpio.gpioTerminate()


def IRBlast(tankID, projectile_type, verbose=False):
	if projectile_type == "LASER":
		projectile_id = 0xF1
	else:
		if verbose:
			print("unknown projectile type")
		return False

	msg = (str(bin(projectile_id))[2:] + str(bin(tankID))[2:])
	if verbose:
		print("send :", encodeMsg(msg))
	IR(23, "NEC", dict()).send_code(encodeMsg(msg)+"0")
	# Last bit not receive so we add an artificial one for the actual last bit to be received
	
	return True

#####################################
#           Hamming code            #
#####################################
def calcRedundantBits(data):
	return math.ceil(math.log2(data))


def posRedundantBits(data, r):

	# block parity bit (not used)
	data.insert(0, 0)

	j = 0
	for i in range(1, len(data) + r):
		if(i == 2**j):
			data.insert(i, 0)
			j += 1
	return data

def removeRedundantBits(data, r):
	data.pop(0)

	j = 0
	for i in range(1, len(data)):
		if(i == 2**j):
			data.pop(i - (j+1))
			j += 1
	return data

def calcParityBits(data, r):
	n = len(data)

	# For finding rth parity bit, iterate over
	# 0 to r - 1
	for i in range(r):
		val = 0
		for j in range(1, n + 1):
			# If position has 1 in ith significant
			# position then Bitwise OR the array value
			# to find parity bit value.
			if(j & (2**i) == (2**i)):
				val = val ^ data[j]
		data[2**i] = val
	return data

def encodeMsg(msg):

	data = list(map(int, msg))

	# Hamming(63, 57) ~ (64, 57)
	data.insert(0, 0)

	r = calcRedundantBits(len(data))
	data = posRedundantBits(data, r)
	data = calcParityBits(data, r)

	# Test Error
	# data[23] = int(not data[23])

	data = ''.join(str(x) for x in data)

	return data

def printAsblock(data, blocksize):
	for i in range(blocksize):
		for j in range(blocksize):
			try:
				print(data[(i*blocksize)+j], end=" ")
			except IndexError:
				print(" ", end=" ")
		print()

def detectError(data):
	return reduce(lambda x, y: x ^ y, [i for i, bit in enumerate(data) if bit])


def signalToBinary(signal):
	return "".join(map(lambda signal: "1" if signal[1] > 1000 else "0", filter(lambda signal: signal[0] == 1, signal)))

def getSignal(channel, verbose=True):
	shooter = None
	r = 6

	value = 0

	# Grab the start time of the command
	startTime = datetime.now()

	# Used to buffer the command pulses
	command = []

	# The end of the "command" happens when we read more than
	# a certain number of 1s (1 is off for my IR receiver)
	numOnes = 0

	# Used to keep track of transitions from 1 to 0
	previousVal = 0
	print("arrived here");

	while True:

		if value != previousVal:
			# The value has changed, so calculate the length of this run
			now = datetime.now()
			pulseLength = now - startTime
			startTime = now

			command.append((previousVal, pulseLength.microseconds))

		if value:
			numOnes = numOnes + 1
		else:
			numOnes = 0

		# 10000 is arbitrary, adjust as necessary
		if numOnes > 10000:
			break

		previousVal = value
		value = GPIO.input(channel)

	data = list(map(int, signalToBinary(command)[2:]))
	if verbose:
		if data != []:
			print("r : " + ''.join(str(num) for num in data))
	if len(data) == 64:
		correction = detectError(data)
		if(correction!=0):
			data[correction] = int(not data[correction])
			if verbose:
				print("Error detected and fixed")

		data = removeRedundantBits(data, r)

		shooter = hex(int(str(''.join(str(x) for x in data)),2))
		return shooter