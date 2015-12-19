event_types = ["data", "config", "decode_error"]

event_ids = {
	"data"         : ["speed", "coords", "accel", "time", "text"],
	"config"       : ["mode_text"],
	"decode_error" : ["data_corrupt", "data_missing"]
}

class EventException(Exception):
	pass