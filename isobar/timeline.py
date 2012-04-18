import time
import math
import copy
import thread
from isobar import *
from isobar.pattern import *

import isobar.io

class Timeline:
	CLOCK_INTERNAL = 0
	CLOCK_EXTERNAL = 1

	def __init__(self, bpm = 120, device = None):
		"""expect to receive one tick per beat, generate events at 120bpm"""
		self.ticklen = 1/24.0
		self.beats = 0
		self.device = device
		self.channels = []
		self.automators = []

		self.debug = False
		self.bpm = None
		self.clock = None
		self.clocksource = None
		self.thread = None

		self.events = []

		if hasattr(bpm, "clocktarget"):
			bpm.clocktarget = self
			self.clocksource = bpm
			self.clockmode = self.CLOCK_EXTERNAL
		else:
			self.bpm = bpm
			self.clock = Clock(60.0 / self.bpm / 24.0)
			self.clockmode = self.CLOCK_INTERNAL
		
	def tick(self):
		#------------------------------------------------------------------------
		# some devices (ie, MidiFileOut) require being told to tick
		#------------------------------------------------------------------------
		self.device.tick(self.ticklen)

		#------------------------------------------------------------------------
		# copy self.channels because removing from it whilst using it = bad idea
		#------------------------------------------------------------------------
		for channel in self.channels[:]:
			channel.tick(self.ticklen)
			if channel.finished:
				self.channels.remove(channel)

		#------------------------------------------------------------------------
		# TODO: should automator and channel inherit from a common superclass?
		#       one is continuous, one is discrete.
		#------------------------------------------------------------------------
		for automator in self.automators[:]:
			automator.tick(self.ticklen)
			if automator.finished:
				self.automators.remove(automator)

		self.beats += self.ticklen

		#------------------------------------------------------------------------
		# copy self.events because removing from it whilst using it = bad idea
		#------------------------------------------------------------------------
		for event in self.events[:]:
			#------------------------------------------------------------------------
			# round needed because we can sometimes end up with beats = 3.99999999...
			# http://docs.python.org/tutorial/floatingpoint.html
			#------------------------------------------------------------------------
			if round(event["time"], 8) <= round(self.beats, 8):
				event["fn"]()
				self.events.remove(event)

	def reset_to_beat(self):
		self.beats = round(self.beats) # + 1/24.0
		for channel in self.channels:
			channel.reset_to_beat()

	def reset(self):
		# print "tl reset!"
		self.beats = -.0001
		# XXX probably shouldn't have to do this - should channels read the tl ticks value?
		for channel in self.channels:
			channel.reset()

	def background(self):
		self.thread = thread.start_new_thread(self.run, ())

	def run(self):
		# create clock with 64th-beat granularity
		if self.clockmode == self.CLOCK_INTERNAL:
			self.clock.run(self)
		else:
			self.clocksource.run()

	def warp(self, warper):
		self.clock.warp(warper)

	def unwarp(self, warper):
		self.clock.warp(warper)

	def output(self, device):
		self.device = device

	def sched(self, event, quantize = 0):
		if not self.device:
			self.device = isobar.io.MidiOut()

		# hmm - why do we need to copy this?
		# c = channel(copy.deepcopy(dict))
		# c = Channel(copy.copy(dict))
		def addchan():
			#----------------------------------------------------------------------
			# this isn't exactly the best way to determine whether a device is
			# an automator or event generator. should we have separate calls?
			#----------------------------------------------------------------------
			if type(event) == dict and event.has_key("control"):
				pass
			else:
				c = Channel(event)
				c.device = self.device
				self.channels.append(c)

		if quantize:
			schedtime = quantize * math.ceil(float(self.beats) / quantize)
			self.events.append({ 'time' : schedtime, 'fn' : addchan })
		else:
			addchan()

class AutomatorChannel:
	def __init__(self, dict = {}):
		dict.setdefault('value', 0.5)
		dict.setdefault('control', 0)
		dict.setdefault('channel', 0)

		for k, value in dict.iteritems():
			if not isinstance(value, Pattern):
				dict[k] = PAConst(value)

		self.dick = dict

	def tick(self, ticklen):
		pass	

class Channel:
	def __init__(self, events = {}):
		#----------------------------------------------------------------------
		# evaluate in case we have a pattern which gives us an event.
		#----------------------------------------------------------------------
		self.events = Pattern.pattern(events)

		self.next()

		self.pos = 0
		self.dur_now = 0
		self.phase_now = self.event["phase"].next()
		self.next_note = 0

		self.noteOffs = []
		self.finished = False

	def next(self):
		event = Pattern.value(self.events)
		event.setdefault('note', 60)
		event.setdefault('transpose', 0)
		event.setdefault('dur', 1)
		event.setdefault('amp', 64)
		event.setdefault('channel', 0)
		event.setdefault('omit', 0)
		event.setdefault('gate', 1.0)
		event.setdefault('phase', 0.0)
		event.setdefault('octave', 0)

		if event.has_key('key'):
			pass
		elif event.has_key('scale'):
			event['key'] = Key(0, event['scale'])
		else:
			event['key'] = Key(0, Scale.major)

		#----------------------------------------------------------------------
		# might be nice to create a event subclass which automatically
		# creates pconsts when integer values are requested
		#----------------------------------------------------------------------
		for key, value in event.items():
			event[key] = Pattern.pattern(value)

		self.event = event

	def tick(self, time):
		#----------------------------------------------------------------------
		# process noteOffs before we play the next note, else notes
		# with gate = 1.0 will immediately be cancelled.
		#----------------------------------------------------------------------
		self.processNoteOffs()

		try:
			if round(self.pos, 8) >= round(self.next_note + self.phase_now, 8):
				self.dur_now = self.event['dur'].next()
				self.phase_now = self.event['phase'].next()

				self.play()

				self.next_note += self.dur_now

				self.next()
		except StopIteration:
			self.finished = True

		self.pos += time

	def reset_to_beat(self):
		self.pos = round(self.pos) # + 1/24.0

	def reset(self):
		self.pos = 0
		self.dur_now = 0
		self.next_note = 0

	def play(self):
		if self.event.has_key("print"):
			value = Pattern.value(self.event["print"])
			print value

		if self.event.has_key("action"):
			Pattern.value(self.event["action"])
			return

		note = None

		if self.event.has_key("degree"):
			degree = self.event['degree'].next()
			key = self.event['key'].next()
			octave = self.event['octave'].next()
			if not degree is None:
				note = key[degree] + (octave * 12)
		else:
			note = self.event['note'].next()

		if note is None:
			# print "(rest)"
			return

		note   += self.event['transpose'].next()
		amp     = self.event['amp'].next()
		channel = self.event['channel'].next()

		if random.uniform(0, 1) < self.event['omit'].next():
			return

		# print "note %d (%d)" % (note, amp)
		self.device.noteOn(note, amp, channel)

		gate = self.event['gate'].next()
		note_dur = self.dur_now * gate
		self.schedNoteOff(self.next_note + note_dur + self.phase_now, note, channel)

	def schedNoteOff(self, time, note, channel):
		self.noteOffs.append([ time, note, channel ])

	def processNoteOffs(self):
		for n, note in enumerate(self.noteOffs):
			if note[0] <= self.pos:
				self.device.noteOff(note[1], note[2])
				self.noteOffs.pop(n)

#----------------------------------------------------------------------
# a clock is relied upon to generate accurate tick() events every
# fraction of a note. it should handle millisecond-level jitter
# internally - ticks should always be sent out on time!
#
# period, in seconds, corresponds to a 24th crotchet (1/96th of a bar),
# as per MIDI
#----------------------------------------------------------------------

class Clock:
	def __init__(self, ticksize = 1/24.0):
		self.ticksize_orig = ticksize
		self.ticksize = ticksize
		self.warpers = []
		self.accelerate = 1.0

	def run(self, timeline):
		clock0 = clock1 = time.time() * self.accelerate
		try:
			timeline.tick()
			while True:
				if clock1 - clock0 >= self.ticksize:
					# time for a tick
					timeline.tick()
					clock0 += self.ticksize
					self.ticksize = self.ticksize_orig
					for warper in self.warpers:
						warp = warper.next()
						if warp > 0:
							self.ticksize *= (1.0 + warp)
						elif warp < 0:
							self.ticksize /= (1.0 - warp)

				time.sleep(0.0001)
				clock1 = time.time() * self.accelerate
		except KeyboardInterrupt:
			print "interrupt caught, exiting"
			return

	def warp(self, warper):
		self.warpers.append(warper)

	def unwarp(self, warper):
		self.warpers.remove(warper)

