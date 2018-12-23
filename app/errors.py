import time


class ErrorResponse(Exception):
    http_code = 400

    def __init__(self, message, http_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if http_code is not None:
            self.http_code = http_code
        self.payload = payload

    def to_dict(self):
        dict_response = dict(self.payload or ())
        dict_response['message'] = self.message
        dict_response['timestamp'] = time.strftime("%c")
        dict_response['status'] = False
        return dict_response


class DatabaseException(Exception):
    def __init__(self, error_details):
        Exception.__init__(self)
        self.error_details = error_details

    def __str__(self):
        return self.error_details
