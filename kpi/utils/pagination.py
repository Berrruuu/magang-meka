from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "code": 200,
            "message": "Data berhasil diambil",
            "data": data,
            "pagination": {
                "current_page": self.page.number,
                "per_page": self.get_page_size(self.request),
                "total_items": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "has_next_page": self.page.has_next(),
                "has_prev_page": self.page.has_previous(),
            }
        })
