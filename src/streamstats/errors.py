class StreamStatsError(Exception):
    """ Basic error of the streaming file analyzer. """


class UnsupportedFormatError(StreamStatsError):
    """ The file format is not supported by the program. """


class InvalidEventError(StreamStatsError):
    """ Incorrect event detected. """


class InvalidTimestampError(StreamStatsError):
    """ Incorrect timestamp detected. """


class CLIConfigError(StreamStatsError):
    """ ClI configuration error. """
