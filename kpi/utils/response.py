def success_response(data=None, message="Success", code=200, pagination=None):
    response = {
        "status": "success",
        "code": code,
        "message": message,
        "data": data
    }

    if pagination:
        response["pagination"] = pagination

    return response
