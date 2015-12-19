import decoder_events

"""AbstractDataDecoder class, used as the base class for all data decoders."""
class AbstractDataDecoder:

	def __init__(self, event_callback):
		self._event_callback = event_callback

	def event(self, event_type, event_id, event_data):
		"""Fire an event. This function is the standard way to pass decoded data from the decoder, pass on errors and show camera configuration."""
		if event_type not in decoder_events.event_types:
			raise decoder_events.EventException("No such event type '%s', accepted types are '%s'." % (event_type, ', '.join(decoder_events.event_types)))
		event_ids = decoder_events.event_ids[event_type]
		if event_id not in event_ids:
			raise decoder_events.EventException("Invalid event ID '%s', accepted IDs are '%s'." % (event_id, ', '.join(event_ids)))
		self._event_callback(event_type, event_id, event_data)

	def get_name(self):
		"""This function must return a string with a human readable name to indentify the decoder. 
		Typically this is the name of the supported camera"""
		return "<unknown decoder>"

	def pipeline_attach(self, pipeline):
		"""Attach to the GST pipeline to get access to the data to decode. 
		You must be able to detach when pipeline_detach is called."""
		pass

	def pipeline_detach(self, pipeline):
		"""Detach from the GST pipeline. 
		This will be called if the user swaps to another decoder. 
		You must ensure the pipeline configuration matches what it was when pipeline_attach was called"""
		pass