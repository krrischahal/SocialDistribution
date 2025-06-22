import base64
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.hashers import check_password
from .models import NodeCredential, RemoteNode
from django.contrib.auth.models import AnonymousUser

class NodeBasicAuthentication(BaseAuthentication):
    """
    Custom authentication class to handle node-to-node Basic Authentication.
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Basic '):
            return None  # No authentication attempted

        try:
            # Decode the Basic Auth credentials
            encoded_credentials = auth_header.split(' ')[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
        except (IndexError, ValueError, base64.binascii.Error):
            raise exceptions.AuthenticationFailed('Invalid Authorization header.')

        # Check against local node credentials
        try:
            local_credential = NodeCredential.objects.get(username=username)
            print(local_credential.password)
            print(password)
            if check_password(password, local_credential.password):
                return (AnonymousUser(), None)
        except NodeCredential.DoesNotExist:
            pass  

        # If no credentials match
        raise exceptions.AuthenticationFailed('Invalid username/password.')
