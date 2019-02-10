from datetime import datetime

from Crypto.Hash import SHA256, HMAC as HASH_HMAC

from src.connection.base import ConnectionBase


class HMAC(ConnectionBase):

    def __init__(self, public_key, private_key):
        self._publicKey = public_key
        self._privateKey = private_key

    def _modify_request(self, request):
        date_stamp = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        request.headers['Date'] = date_stamp
        msg = f'{request.method}/{request.route}{date_stamp}{self._publicKey}'.encode(
            encoding='utf-8')
        h = HASH_HMAC.new(self._privateKey.encode(encoding='utf-8'), msg, SHA256)
        signature = h.hexdigest()
        request.headers['Authorization'] = f'hmac {self._publicKey}:{signature}'
