class Response:
    def __init__(self, code, response):
        self.code = code
        self.response = response


class Request:
    def __init__(self, method, route, data, headers):
        self.method = method
        self.route = route
        self.headers = headers
        self.data = data


class ResponseException(Exception):
    def __init__(self, code, response):
        self.code = code
        self.response = response


class AuthorizationException(ResponseException):
    pass
