from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class AuthorPagination(PageNumberPagination):
    page_size_query_param = 'size'
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'type': 'authors',
            'authors': data,
            'page': self.page.number,
            'size': self.page.paginator.per_page,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count
        })