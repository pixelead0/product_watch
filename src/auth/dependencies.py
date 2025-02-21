import logging
from typing import Callable, Optional

import redis
from django.conf import settings
from django.http import HttpRequest
from ninja.security import HttpBearer

from auth.jwt import JWTHandler
from auth.models import User

logger = logging.getLogger("auth")


class AuthBearer(HttpBearer):
    def __init__(self, redis_client: Optional[redis.Redis] = None, require_admin: bool = False) -> None:
        self.jwt_handler = JWTHandler()
        self.require_admin = require_admin
        self.redis_client = redis_client or redis.Redis(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            db=int(settings.REDIS_DB),
            decode_responses=True,
        )
        logger.info(f"AuthBearer inicializado, require_admin: {require_admin}")

    def authenticate(self, request: HttpRequest, token: str) -> Optional[User]:
        logger.info(f"Autenticando solicitud a: {request.path}")
        logger.info(f"Token recibido: {token[:20]}...")
        payload = self.jwt_handler.verify_token(token)
        if not payload:
            logger.warning("Verificación de token falló")
            return None

        logger.info(f"Payload del token: {payload}")

        # Check rate limit
        client_ip = request.META.get("REMOTE_ADDR", "unknown")
        request_key = f"rate_limit:{client_ip}:{request.path}"

        try:
            current_count = self.redis_client.incr(request_key)
            if current_count == 1:
                # Set expiration for new keys (1 hour)
                self.redis_client.expire(request_key, 3600)

            # Get rate limit for this endpoint (default: 100/hour)
            rate_limit = getattr(settings, "RATE_LIMIT", {}).get("DEFAULT", "100/hour")
            max_requests = int(rate_limit.split("/")[0])

            logger.info(f"Rate limit: {current_count}/{max_requests}")

            if current_count > max_requests:
                logger.warning(f"Rate limit excedido: {current_count}/{max_requests}")
                return None
        except Exception as e:
            logger.error(f"Error en rate limiting: {str(e)}")

        try:
            user = User.objects.get(id=payload.sub)
            logger.info(f"Usuario encontrado: {user.id}, is_admin: {user.is_admin}")

            # Check admin requirement
            if self.require_admin and not user.is_admin:
                logger.warning(f"Usuario {user.id} no es admin pero se requiere admin")
                return None

            # Attach user to request
            request.user = user
            logger.info(f"Autenticación exitosa para usuario: {user.id}")
            return user
        except User.DoesNotExist:
            logger.error(f"Usuario no encontrado: {payload.sub}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en authenticate: {str(e)}")
            return None


# Convenience functions for route authorization
def get_admin_auth() -> Callable:
    return AuthBearer(require_admin=True)


def get_user_auth() -> Callable:
    return AuthBearer(require_admin=False)
