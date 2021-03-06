#
# Copyright (c) 2020 Carlos Fernández Sánchez and Raúl Caro Teixidó.
#
# This file is part of Mística 
# (see https://github.com/IncideDigital/Mistica).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from sotp.misticathread import ServerWrapper
from base64 import urlsafe_b64encode,urlsafe_b64decode
from wrapper.server.wrap_server.httpserver import httpserver

class httpwrapper(ServerWrapper):

    SERVER_CLASS = httpserver
    NAME = "http"
    CONFIG = {
        "prog": "http",
        "wrapserver": "httpserver",
        "description": "Encodes/Decodes data in HTTP requests/responses using different methods",
        "args": [
            {
                "--method": {
                    "help": "HTTP Method to use",
                    "nargs": 1,
                    "default": ["GET"],
                    "choices": ["GET","POST"],
                    "type": str
                },
                "--uri": {
                    "help": "URI Path before data message",
                    "nargs": 1,
                    "default": ["/"],
                    "type": str
                },
                "--header": {
                    "help": "Header key for encapsulate data message",
                    "nargs": 1,
                    "type": str
                },
                "--post-field": {
                    "help": "Post Field for encapsulate data message",
                    "nargs": 1,
                    "type": str
                },
                "--success-code": {
                    "help": "HTTP Code for Success Connections. Default is 200",
                    "nargs": 1,
                    "default": [200],
                    "choices": [100,101,102,200,201,202,203,204,205,206,207,
                                208,226,300,301,302,303,304,305,306,307,308,
                                400,401,402,403,404,405,406,407,408,409,410,
                                411,412,413,414,415,416,417,418,421,422,423,
                                424,426,428,429,431,500,501,502,503,504,505,
                                506,507,508,510,511],
                    "type":  int
                },
                "--max-size": {
                    "help": "Max size of the SOTP packet. Default is 10000 bytes",
                    "nargs": 1,
                    "default": [10000],
                    "type":  int
                },
                "--max-retries": {
                    "help": "Maximum number of re-synchronization retries.",
                    "nargs": 1,
                    "default": [5],
                    "type":  int
                }
            }
        ]
    }

    def __init__(self, id, qsotp, args, logger):
        ServerWrapper.__init__(self, id, httpwrapper.NAME, qsotp, httpwrapper.SERVER_CLASS.NAME, args,logger)
        # Logger parameters
        self.logger = logger
        self._LOGGING_ = False if logger is None else True

    def parseArguments(self, args):
        parsed = self.argparser.parse_args(args.split())
        self.method = parsed.method[0]
        self.header = parsed.header[0] if parsed.header is not None else None
        self.uri = parsed.uri[0]
        self.post_field = parsed.post_field[0] if parsed.post_field is not None else None
        self.max_size = parsed.max_size[0]
        self.max_retries = parsed.max_retries[0]
        self.success_code = parsed.success_code[0]

    def unpackSotp(self, data):
        # We use base64_urlsafe_encode, change if you encode different.
        return urlsafe_b64decode(data)

    def parseFromHeaders(self, content):
        try:
            for key,value in content.items():
                if key == self.header:
                    return self.unpackSotp(value)
            return None
        except Exception:
            return None

    def parseFromURI(self, requestline):
        try:
            _,uri,_ = requestline.split(' ')
            sotpdata = uri.replace(self.uri,'')
            return self.unpackSotp(sotpdata)
        except Exception:
            return None

    def parseFromPostFields(self, fields):
        try:
            for field in fields.list:
                if field.name == self.post_field:
                    return self.unpackSotp(field.value)
            return None
        except Exception:
            return None

    def parseGET(self, content):
        if self.header:
            return self.parseFromHeaders(content['headers'])
        else:
            return self.parseFromURI(content['requestline'])

    def parsePOST(self, content):
        if self.header:
            return self.parseFromHeaders(content['headers'])
        elif self.post_field:
            return self.parseFromPostFields(content['content'])
        else:
            return self.parseFromURI(content['requestline'])

    def unwrap(self, content):
        if self.method == "GET":
            unwrapped = self.parseGET(content)
        else:
            unwrapped = self.parsePOST(content)
        return unwrapped

    def generateResponse(self,content):
        return {
            "requestline" : "",
            "headers" : {},
            "content" : content,
            "httpcode" : self.success_code
        }

    def wrap(self, content):
        urlSafeEncodedBytes = urlsafe_b64encode(content)
        urlSafeEncodedStr = str(urlSafeEncodedBytes, "utf-8")
        return self.generateResponse(urlSafeEncodedStr)
