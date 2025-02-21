import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Union
from uuid import UUID

import redis
from django.conf import settings
from jose import JWTError, jwt

from auth.schemas import TokenPayload

logger = logging.getLogger("auth")


class JWTHandler:
    def __init__(self) -> None:
        logger.info("Inicializando JWTHandler")
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            db=int(settings.REDIS_DB),
            decode_responses=True,
        )
        self.jwt_secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        try:
            ping_result = self.redis_client.ping()
            logger.info(f"Conexión a Redis: {'Exitosa' if ping_result else 'Fallida'}")
        except Exception as e:
            logger.error(f"Error al conectar con Redis: {str(e)}")

    def create_access_token(self, user_id: Union[str, UUID], is_admin: bool) -> str:
        """
        Create a JWT access token.
        """
        logger.info(f"Creando token para usuario: {user_id}, is_admin: {is_admin}")
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "exp": expire.timestamp(),
            "iat": time.time(),
            "is_admin": is_admin,
        }
        token = jwt.encode(payload, self.jwt_secret_key, algorithm=self.algorithm)

        # Store token metadata in Redis
        token_key = f"token:{user_id}"
        token_data = {
            "user_id": str(user_id),
            "exp": str(int(expire.timestamp())),
            "is_admin": str(is_admin).lower(),
        }

        try:
            # Guardar en Redis
            self.redis_client.hmset(token_key, token_data)
            self.redis_client.expireat(token_key, int(expire.timestamp()))

            # Verificar que se guardó correctamente
            stored_data = self.redis_client.hgetall(token_key)
            logger.info(f"Token almacenado en Redis: {token_key} -> {stored_data}")
            if not stored_data:
                logger.error(f"El token NO se almacenó correctamente en Redis: {token_key}")
        except Exception as e:
            logger.error(f"Error al guardar token en Redis: {str(e)}")

        return token

    def create_refresh_token(self, user_id: Union[str, UUID]) -> str:
        """
        Create a JWT refresh token.
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": str(user_id),
            "exp": expire.timestamp(),
            "iat": time.time(),
            "type": "refresh",
        }
        token = jwt.encode(payload, self.jwt_secret_key, algorithm=self.algorithm)

        # Store refresh token in Redis
        refresh_key = f"refresh_token:{user_id}"
        self.redis_client.set(refresh_key, token)
        self.redis_client.expireat(refresh_key, int(expire.timestamp()))

        return token

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """
        Verify a JWT token.
        """

        try:
            # Verificar firma JWT
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.algorithm])
            token_data = TokenPayload(**payload)

            # Verificar en Redis si está disponible
            user_id = payload.get("sub")
            token_key = f"token:{user_id}"

            try:
                exists = self.redis_client.exists(token_key)
                if exists:
                    # Token válido en Redis
                    stored_data = self.redis_client.hgetall(token_key)
                    logger.info(f"Token validado en Redis: {token_key}")
                else:
                    logger.warning(f"Token no encontrado en Redis: {token_key}")
                    if settings.STRICT_TOKEN_VALIDATION:
                        return None
                    logger.warning("Modo estricto desactivado: aceptando token JWT sin verificación en Redis")
            except Exception as e:
                # Error al verificar en Redis
                logger.error(f"Error al verificar token en Redis: {str(e)}")
                if settings.STRICT_TOKEN_VALIDATION:
                    return None
                logger.warning("Modo estricto desactivado: aceptando token JWT debido a error en Redis")

            return token_data
        except JWTError as e:
            logger.error(f"Error al verificar token JWT: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en verify_token: {str(e)}")
            return None

    def verify_token0(self, token: str) -> Optional[TokenPayload]:
        """
        Verify a JWT token.
        """
        logger.info(f"Verificando token: {token[:20]}...")
        try:
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.algorithm])
            logger.info(f"Token decodificado: {payload}")

            token_data = TokenPayload(**payload)
            logger.info(f"TokenPayload creado: {token_data}")

            # Check if token is in Redis
            user_id = payload.get("sub")
            token_key = f"token:{user_id}"

            try:
                exists = self.redis_client.exists(token_key)
                if exists:
                    stored_data = self.redis_client.hgetall(token_key)
                    logger.info(f"Token encontrado en Redis: {token_key} -> {stored_data}")
                else:
                    logger.warning(f"Token NO encontrado en Redis: {token_key}")
                    return None
            except Exception as e:
                logger.error(f"Error al verificar token en Redis: {str(e)}")
                # En caso de error de Redis, podríamos aceptar el token JWT
                # Descomentar para desarrollo si hay problemas con Redis
                # logger.warning("Aceptando token JWT debido a error de Redis")
                # return token_data
                return None

            return token_data
        except JWTError as e:
            logger.error(f"Error al verificar token JWT: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en verify_token: {str(e)}")
            return None

    def verify_refresh_token(self, token: str) -> Optional[str]:
        """
        Verify a JWT refresh token and return the user_id.
        """
        try:
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.algorithm])

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            refresh_key = f"refresh_token:{user_id}"

            # Check if refresh token matches the one in Redis
            stored_token = self.redis_client.get(refresh_key)
            if not stored_token or stored_token != token:
                return None

            return user_id
        except JWTError:
            return None

    def invalidate_tokens(self, user_id: Union[str, UUID]) -> None:
        """
        Invalidate all tokens for a user.
        """
        token_key = f"token:{user_id}"
        refresh_key = f"refresh_token:{user_id}"
        self.redis_client.delete(token_key, refresh_key)
