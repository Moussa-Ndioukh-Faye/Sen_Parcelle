# ══════════════════════════════════════════════════════════════
# MIDDLEWARE AUDIT — Log automatique des requêtes sensibles
# apps/audit/middleware.py
# ══════════════════════════════════════════════════════════════

SENSITIVE_PATHS = {
    "/api/auth/login/",
    "/api/auth/inscription/",
    "/api/parcelles/",
    "/api/transactions/",
    "/api/utilisateurs/",
}

SENSITIVE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware:
    """
    Middleware qui logue automatiquement les requêtes sensibles.
    Ajoute IP + user-agent + durée d'exécution.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._audit       = AuditService()

    def __call__(self, request):
        start_time = time.time()
        response   = self.get_response(request)
        duration   = round((time.time() - start_time) * 1000, 2)   # ms

        # Logguer uniquement les routes sensibles
        should_log = (
            any(request.path.startswith(p) for p in SENSITIVE_PATHS)
            and request.method in SENSITIVE_METHODS
        )

        if should_log and hasattr(request, "user") and request.user.is_authenticated:
            self._audit.log(
                user_id=str(request.user.id),
                action=f"api_{request.method.lower()}",
                metadata={
                    "path":         request.path,
                    "method":       request.method,
                    "status_code":  response.status_code,
                    "duration_ms":  duration,
                },
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:200],
            )

        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        """
        Récupère la vraie IP client (derrière Nginx/load balancer).
        """
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")