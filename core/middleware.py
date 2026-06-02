class ContentSecurityPolicyMiddleware:
    """
    Content-Security-Policy header qo'shadi.
    Sayt CDNlari: Tailwind (cdn.tailwindcss.com), Chart.js (cdn.jsdelivr.net),
    Google Fonts (fonts.googleapis.com, fonts.gstatic.com).
    Django admin va inline skriptlar uchun 'unsafe-inline' kerak.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._policy = "; ".join([
            "default-src 'self'",
            "script-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net 'unsafe-inline'",
            "style-src 'self' https://cdn.tailwindcss.com https://fonts.googleapis.com 'unsafe-inline'",
            "font-src 'self' https://fonts.gstatic.com data:",
            "img-src 'self' data: blob: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ])

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = self._policy
        return response
