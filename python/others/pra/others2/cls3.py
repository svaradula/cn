class APIRequest:
    _request_count = 0

    def __init__(self):
        APIRequest._request_count += 1

    @classmethod
    def total_requests(cls):
        return cls._request_count


r1 = APIRequest()
r2 = APIRequest()

print(APIRequest.total_requests())  # 2
