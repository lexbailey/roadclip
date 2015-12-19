import abstract_decoder

class NoDecoder(abstract_decoder.AbstractDataDecoder):

	def get_name(self):
		return "No Decoder"