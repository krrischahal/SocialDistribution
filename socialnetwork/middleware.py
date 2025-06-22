# socialnetwork/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.hashers import check_password
from .models import NodeCredential
import base64

# socialnetwork/middleware.py
import logging

logger = logging.getLogger(__name__)

class NodeCorsMiddleware(MiddlewareMixin):
    """
    Middleware to dynamically allow CORS for authenticated nodes.
    """

    def process_response(self, request, response):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            try:
                # Decode the Basic Auth credentials
                encoded_credentials = auth_header.split(' ')[1]
                decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
                username, password = decoded_credentials.split(':', 1)
                local_credential = NodeCredential.objects.get(username=username)
                if check_password(password, local_credential.password):
                    origin = request.headers.get('Origin')
                    if origin:
                        response['Access-Control-Allow-Origin'] = origin
                        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
                        logger.info(f"CORS headers set for origin: {origin}")
            except (IndexError, ValueError, base64.binascii.Error, NodeCredential.DoesNotExist) as e:
                logger.error(f"Failed to set CORS headers: {e}")

        return response

