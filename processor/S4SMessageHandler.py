__author__ = 'Musa Morena Marcusso Manhaes'


class S4SMessageHandler:
    _MESSAGE_TYPES = {'warning': 'Warning',
                      'error': 'Error',
                      'info': 'Information'}
    _INSTANCE = None

    def __init__(self):
        self._callback = None

    @classmethod
    def get_instance(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = S4SMessageHandler()
        return cls._INSTANCE

    def set_callback(self, fcn):
        self._callback = fcn

    def push_message(self, class_name, message_type, message):
        if message_type not in self._MESSAGE_TYPES.keys():
            raise KeyError('Invalid message type')
        if type(class_name) is not str or type(message) is not str:
            raise TypeError('Class name and message must be strings, class_name=' + str(class_name) + ', message=' +
                            str(message))

        if self._callback is not None:
            mess_type = ''
            if message_type == 'error':
                mess_type = 'Error: '
            elif message_type == 'warning':
                mess_type = 'Warning: '
            self._callback(mess_type + message)
