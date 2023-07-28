import ipaddress

class RestrictIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_ips = [ipaddress.ip_network('10.8.0.0/24')]

    def __call__(self, request):
        client_ip = ipaddress.IPv4Address(request.META.get('REMOTE_ADDR'))
        if not any(client_ip in ip_range for ip_range in self.allowed_ips):
            return HttpResponseForbidden("Access denied. Your IP is not allowed.")
        return self.get_response(request)
