import abstract_decoder

class NoDataDecoder(abstract_decoder.AbstractDataDecoder):

	@staticmethod
	def get_label():
		return "No Decoder (Disable data features)"