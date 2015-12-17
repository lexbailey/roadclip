#!/usr/bin/python

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk, GdkX11, GstVideo, GstBase

import pygtk

GObject.threads_init()
Gst.init(None)

class SubDataSink(GstBase.BaseSink):
	__gstmetadata__ = ('SubDataSink','Sink', 'Subtitle Data Sink Element', 'Daniel Bailey')

	__gsttemplates__ = Gst.PadTemplate.new("sink",
										Gst.PadDirection.SINK,
										Gst.PadPresence.ALWAYS,
										Gst.Caps.new_any())

	def do_render(self, buffer):
		#print("timestamp(buffer):%s" % (Gst.TIME_ARGS(buffer.pts)))
		print(buffer.extract_dup(0, buffer.get_size()))
		return Gst.FlowReturn.OK


class Main:

	def get_handy_widgets(self, widgets):
		for widget in widgets:
			setattr(self, widget, self.builder.get_object(widget))

	def __init__(self):

		# initialise State
		self.is_playing = False
		self.was_playing = False
		self.window_handle = 0

		# Load gui from gui.glade
		self.builder = Gtk.Builder()
		self.builder.add_from_file("gui.glade")
		self.builder.connect_signals(self)
		
		# Gstreamer init
		#self.pipeline = gst.Pipeline("mypipeline")

		# Test video input
		self.videosrc = Gst.ElementFactory.make("playbin", "video")
		assert self.videosrc != None, ("Unable to create xvimagesink element.")
		
		# Start listening to the bus
		self.bus = self.videosrc.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message::tag", self.on_bus_tag)
		self.bus.connect("message", self.on_message)

		# XV image sink, for drawing video on an X window
		self.sink = Gst.ElementFactory.make('xvimagesink', 'videosink')
		assert self.sink != None, ("Unable to create xvimagesink element.")
		self.videosrc.set_property("video-sink", self.sink)

		#self.sub_parser = Gst.ElementFactory.make('subparse', 'subdata')
		#assert self.sub_parser != None, ("Unable to create subparse element.")
		self.sub_data_sink = SubDataSink()
		#self.videosrc.set_property("text-sink", self.sub_parser)
		self.videosrc.set_property("text-sink", self.sub_data_sink)
		#self.sub_parser.link(self.sub_data_sink)

		# Get the various widgets that we need to have handy
		self.get_handy_widgets([
				"videoAspectFrame",
				"videoDrawingArea",
				"fileChooser",
				"seekBar"
			])

		# Get the main window and show it
		self.window = self.builder.get_object("MainWindow")
		self.window.show_all()

		# The pipeline has been constructed, set state to ready.
		self.videosrc.set_state(Gst.State.READY)
		self.openVideoFile("/home/daniel/roadclip/RawNormal.MP4")

		
	def on_bus_tag(self, bus, message):
		taglist = message.parse_tag()
		#put the keys in the dictionary
		#for key in taglist.keys():
		#	print("%s = %s" % (key, taglist[key]))
		#print("Got message %r, dir is %s\n type is %s" % (message, dir(message), message.type))

	def on_message(self, bus, message):
		#print(message.type)
		#if message.type == Gst.MessageType.WARNING:
		#	print(message.parse_warning())
		#print("%r" % (message))
		pass

	def do_play(self):
		self.is_playing = True
		GObject.timeout_add(100, self.update_slider)
		self.videosrc.set_state(Gst.State.PLAYING)

	def do_pause(self):
		self.is_playing = False
		self.videosrc.set_state(Gst.State.PAUSED)

	def on_play_clicked(self, widget):
		self.numVidStreams = self.videosrc.get_property("n-video")
		print("Num vid streams: %d" % (self.numVidStreams))
		self.do_play()

	def on_stop_clicked(self, widget):
		self.do_pause()

	def on_main_window_delete(self, widget, event):
		Gtk.main_quit()
		return False

	def on_videoDrawingArea_realize(self, widget):
		self.window_handle = (widget.get_window().get_xid())
		self.sink.set_window_handle(self.window_handle)

	def openVideoFile(self, fileName):
		print("Loading file '%s'" % (fileName))
		self.videosrc.set_property("uri", "file://" + fileName)
		self.do_pause()
		self.videosrc.get_state(5000000000) #TODO make this better
		self.numVidStreams = self.videosrc.get_property("n-video")
		print("Num vid streams: %d" % (self.numVidStreams))
		pad    = self.videosrc.emit('get-video-pad',0)
		if pad:
			caps   = pad.get_current_caps()
			if caps:
				width  = -1
				height = -1
				for cap in caps:
					print(cap)
					if  cap.has_field("width") and cap.has_field("height"):
						width  = cap["width"]
						height = cap["height"]

				if width > 0 and height > 0:
					print("Video size is %dx%d" % (width, height))
					ratio = float(width)/float(height)
					print("Setting aspect ratio to %f" % (ratio))
					self.videoAspectFrame.set(xalign=0.5, yalign=0.5, ratio=ratio, obey_child=False)

		self.do_play()

	def on_btnFileChooserOpen_clicked(self, widget):
		self.fileChooser.hide()
		filename = self.fileChooser.get_filename()
		self.openVideoFile(filename)
		

	def on_fileChooser_file_activated(self, widget):
		self.on_btnFileChooserOpen_clicked(None)

	def on_btnFileChooserClose_clicked(self, widget):
		self.fileChooser.hide()

	def on_actOpenFile_activate(self, action):
		self.fileChooser.show_all()

	def update_slider(self):
		if not self.is_playing:
			return False # cancel timeout

		try:
			ignore, nanosecs = self.videosrc.query_position(Gst.Format.TIME)
			ignore, duration_nanosecs = self.videosrc.query_duration(Gst.Format.TIME)

			# block seek handler so we don't seek when we set_value()
			self.seekBar.handler_block_by_func(self.on_seekBar_value_changed)

			self.seekBar.set_range(0, float(duration_nanosecs) / Gst.SECOND)
			self.seekBar.set_value(float(nanosecs) / Gst.SECOND)

			self.seekBar.handler_unblock_by_func(self.on_seekBar_value_changed)

		except Exception as e:
			pass

		return True # continue calling update function

	def on_seekBar_value_changed(self, slider):
		seek_time_secs = slider.get_value()
		self.videosrc.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, seek_time_secs * Gst.SECOND)

	def on_seekBar_button_press_event(self, widget, event):
		self.was_playing = self.is_playing
		if self.is_playing:
			self.do_pause()

	def on_seekBar_button_release_event(self, widget, event):
		if self.was_playing:
			self.do_play()

instance=Main()
Gtk.main()