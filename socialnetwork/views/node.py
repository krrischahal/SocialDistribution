from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from socialnetwork.models import NodeCredential, RemoteNode
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class NodeCredentialView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve the first node credential.",
        responses={
            200: openapi.Response(
                description="Node credential retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "username": openapi.Schema(type=openapi.TYPE_STRING, description="Username of the node credential"),
                        "password": openapi.Schema(type=openapi.TYPE_STRING, description="Hashed password (for security reasons, this should not be exposed in production)")
                    }
                )
            ),
            404: openapi.Response(description="No credentials set")
        }
    )
    def get(self, request):
        credential = NodeCredential.objects.first()
        if not credential:
            return Response({"detail": "No credentials set"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "username": credential.username,
            "password": credential.password  # This should be hashed and not exposed in production
        }, status=status.HTTP_200_OK)


class RemoteNodeView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve all remote nodes.",
        responses={
            200: openapi.Response(
                description="List of remote nodes",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "node_url": openapi.Schema(type=openapi.TYPE_STRING, description="URL of the remote node"),
                            "username": openapi.Schema(type=openapi.TYPE_STRING, description="Username associated with the remote node"),
                            "created_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Creation date of the remote node")
                        }
                    )
                )
            )
        }
    )
    def get(self, request):
        nodes = RemoteNode.objects.all().values('node_url', 'username', 'created_at')
        return Response(list(nodes), status=200)

    @swagger_auto_schema(
        operation_description="Add or update a remote node.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['node_url', 'username', 'password'],
            properties={
                'node_url': openapi.Schema(type=openapi.TYPE_STRING, description="URL of the remote node"),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username for the remote node"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Password for the remote node")
            }
        ),
        responses={
            200: openapi.Response(description="Remote node added or updated"),
            400: openapi.Response(description="All fields are required")
        }
    )
    def post(self, request):
        data = request.data
        node_url = data.get('node_url')
        username = data.get('username')
        password = data.get('password')

        if not node_url or not username or not password:
            return Response({"detail": "All fields are required"}, status=400)

        remote_node, created = RemoteNode.objects.update_or_create(
            node_url=node_url,
            defaults={"username": username, "password": password}
        )
        return Response({"detail": "Remote node added or updated"}, status=200)

    @swagger_auto_schema(
        operation_description="Delete a remote node.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['node_url'],
            properties={
                'node_url': openapi.Schema(type=openapi.TYPE_STRING, description="URL of the remote node to be deleted")
            }
        ),
        responses={
            200: openapi.Response(description="Remote node removed"),
            400: openapi.Response(description="Node URL is required"),
            404: openapi.Response(description="Node not found")
        }
    )
    def delete(self, request):
        node_url = request.data.get('node_url')
        if not node_url:
            return Response({"detail": "Node URL is required"}, status=400)

        try:
            remote_node = RemoteNode.objects.get(node_url=node_url)
            remote_node.delete()
            return Response({"detail": "Remote node removed"}, status=200)
        except RemoteNode.DoesNotExist:
            return Response({"detail": "Node not found"}, status=404)
