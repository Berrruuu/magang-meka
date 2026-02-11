from rest_framework.response import Response
from math import ceil

def success_response(
    data,
    message="Sukses",
    status_code=200,
    page=1,
    page_size=10,
    total_items=None
):
    # Jika data list
    if isinstance(data, list):
        total_items = total_items if total_items is not None else len(data)
        total_pages = ceil(total_items / page_size) if page_size else 1
    else:
        # Jika data object tunggal (login, register, logout)
        data = [data]
        total_items = 1
        total_pages = 1
        page = 1
        page_size = 1

    return Response({
        "status": "success",
        "code": status_code,
        "message": message,
        "data": data,
        "pagination": {
            "current_page": page,
            "per_page": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_prev_page": page > 1
        }
    }, status=status_code)


def error_response(message="Terjadi kesalahan", status_code=400, errors=None):
    return Response({
        "status": "error",
        "code": status_code,
        "message": message,
        "errors": errors,
        "pagination": {
            "current_page": 1,
            "per_page": 0,
            "total_items": 0,
            "total_pages": 0,
            "has_next_page": False,
            "has_prev_page": False
        }
    }, status=status_code)
