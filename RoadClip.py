#!/usr/bin/python

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, Gtk, GdkX11, GstVideo, GstBase
import pygtk

GObject.threads_init()
Gst.init(None)

import decoders
from decoders import *


def get_class(module, str):
	return getattr(sys.modules[module], str)

class Main:

	def get_handy_widgets(self, widgets):
		for widget in widgets:
			setattr(self, widget, self.builder.get_object(widget))

	def handle_data_event(self, event_id, event_data):
		#TODO abstract this into data handling classes
		if event_id == "text":
			print(event_data)
		if event_id == "speed":
			self.lblStatus.set_text("Speed: %s" % (event_data))


	def handle_config_event(self, event_id, event_data):
		pass

	def handle_decode_error_event(self, event_id, event_data):
		pass

	def handle_decode_event(self, event_type, event_id, event_data):
		if event_type == "data": self.handle_data_event(event_id, event_data)
		if event_type == "config": self.handle_config_event(event_id, event_data)
		if event_type == "decode_error": self.handle_decode_error_event(event_id, event_data)

	def foo(self):
		pass

	def _init_state(self):
		# initialise State
		self.is_playing    = False
		self.was_playing   = False
		self.window_handle = 0
		self.decoder       = None

	def _init_gui(self):
		# Load gui from gui.glade
		self.builder = Gtk.Builder()
		self.builder.add_from_file("gui.glade")
		self.builder.connect_signals(self)

		# Get the various widgets that we need to have handy
		self.get_handy_widgets([
				"MainWindow",
				"videoAspectFrame",
				"videoDrawingArea",
				"fileChooser",
				"seekBar",
				"lblStatus",
				"decoderMenu"
			])

	def _init_gst_pipeline(self):
		# Gstreamer init

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

		# For now, assume RoadHawk camera
		self.decoder = RoadHawk.RoadHawkDataDecoder(self.handle_decode_event)
		self.decoder.pipeline_attach(self.videosrc)

	def _init_decoder_selection_list(self):
		# Construct the decoder menu from the list of decoders we have
		self.decoder_classes = {}
		self.decoder_menu_items = []
		previtem = None
		for decoder_name in decoders.__all__:
			decoder_string = decoder_name + "DataDecoder"
			self.decoder_classes[decoder_name] = get_class("decoders."+decoder_name, decoder_string)
			newItem = Gtk.RadioMenuItem(label=self.decoder_classes[decoder_name].get_label(), group=previtem)
			newItem.connect("toggled", self.on_decoder_change, decoder_name)
			self.decoder_menu_items.append(newItem)
			previtem = self.decoder_menu_items[-1]

		for decoder_menu_item in self.decoder_menu_items:
			self.decoderMenu.add_child(self.builder, decoder_menu_item, None)

	def select_decoder(self, decoder_name):
		if self.decoder != None:
			self.decoder.pipeline_detach(self.videosrc)
		self.decoder = self.decoder_classes[decoder_name](self.handle_decode_event)
		self.decoder.pipeline_attach(self.videosrc)

	def on_decoder_change(self, widget, name):
		if widget.get_active():
			print("Switch to decoder %s" % (name))
			self.select_decoder(name)

	def _init_decoder(self):
		# TODO get previous / default decoder, instead of just the RoadHawk decoder
		self.select_decoder("RoadHawk")

	def __init__(self):
		self._init_state()
		self._init_gui()
		self._init_gst_pipeline()
		self.videosrc.set_state(Gst.State.READY)
		self._init_decoder_selection_list()
		self._init_decoder()
		
		# Get the main window and show it
		self.MainWindow.show_all()

		# The pipeline has been constructed, set state to ready.
		self.openVideoFile("/home/daniel/roadclip/RawNormal.MP4")

		
	def on_bus_tag(self, bus, message):
		taglist = message.parse_tag()
		#put the keys in the dictionary
		#for key in taglist.keys():
		#   print("%s = %s" % (key, taglist[key]))
		#print("Got message %r, dir is %s\n type is %s" % (message, dir(message), message.type))

	def on_message(self, bus, message):
		#print(message.type)
		#if message.type == Gst.MessageType.WARNING:
		#   print(message.parse_warning())
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