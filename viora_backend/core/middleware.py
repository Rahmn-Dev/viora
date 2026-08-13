class SecurityHeadersMiddleware:
    """
    Inject security headers ke setiap response untuk mencegah popup/tracker
    yang ditembakkan oleh embedded player pihak ketiga (e.g. Vidking).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Permissions-Policy: matikan fitur-fitur yang dipakai popup/tracker
        response['Permissions-Policy'] = (
            'geolocation=(), '
            'camera=(), '
            'microphone=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=(self)'
        )

        # X-Content-Type-Options: cegah MIME sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Referrer-Policy: jangan kirim referrer ke domain luar
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response
