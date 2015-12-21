import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GstBase
import abstract_decoder

class SubDataSink(GstBase.BaseSink):
	__gstmetadata__ = ('SubDataSink','Sink', 'Subtitle Data Sink Element', 'Daniel Bailey')

	__gsttemplates__ = Gst.PadTemplate.new("sink",
										Gst.PadDirection.SINK,
										Gst.PadPresence.ALWAYS,
										Gst.Caps.new_any())

	def set_event_callback(self, event_callback):
		self.event_callback = event_callback

	def decode_metadata(self, data_string):
		table = list('#I8XQWRVNZOYPUTA0B1C2SJ9K.L,M$D3E4F5G6H7')
		data_chars = list(data_string)
		output = ""
		for char in data_chars:
			index = (ord(char)-43)
			if index>=0 and index <len(table):
				output += table[index]
		return output

	def parse_metadata(self, data):
		fields = {}
		for i, text in enumerate(data.split(",")):
			fields[i] = text
		
		output = {}
		# Each data frame contains the following data fields in this order:
		# Accelerometer data, UTS position, camera state, Lat, North/South, Long, East/West, Speed, Unknown, Unknown, Date, Unknown, Checksum (ignored)
		output['Accel'] = fields.get(0, "")
		output['UTS'] = fields.get(1, "")
		output['Status'] = fields.get(2, "")
		output['Lat'] = fields.get(3, "")
		output['NS'] = fields.get(4, "")
		output['Long'] = fields.get(5, "")
		output['EW'] = fields.get(6, "")
		output['Speed'] = fields.get(7, "")
		output['U1'] = fields.get(8, "")
		output['U2'] = fields.get(9, "")
		output['Date'] = fields.get(10, "")
		output['U3'] = fields.get(11, "")
		output['Checksum'] = fields.get(12, "")
			
		return output


	def do_render(self, buffer):
		#print("timestamp(buffer):%s" % (Gst.TIME_ARGS(buffer.pts)))
		raw_data = buffer.extract_dup(0, buffer.get_size())
		format_data = self.parse_metadata(self.decode_metadata(raw_data))
		#self.event_callback("data", "text", str(format_data))
		#testing with speed first
		self.event_callback("data", "speed", format_data["Speed"])
		return Gst.FlowReturn.OK

class RoadHawkDataDecoder(abstract_decoder.AbstractDataDecoder):

	def __init__(self, event_callback):
		abstract_decoder.AbstractDataDecoder.__init__(self, event_callback)
		pass

	@staticmethod
	def get_label():
		return "Road Hawk"

	def pipeline_attach(self, pipeline):
		self.sub_data_sink = SubDataSink()
		self.sub_data_sink.set_event_callback(self.event)
		self.prev_text_sink = pipeline.get_property("text-sink")
		pipeline.set_property("text-sink", self.sub_data_sink)
		pass

	def pipeline_detach(self, pipeline):
		pipeline.set_property("text-sink", self.prev_text_sink)
		pass