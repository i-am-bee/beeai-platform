# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import json
import logging
import os
from datetime import UTC, datetime

import jwt
from fastapi.responses import JSONResponse
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError

logger = logging.getLogger(__name__)

AUDIENCE = os.environ.get("IBM_CLIENT_ID", None)

JWKS_FOLDER = "/jwks"


def get_jwks_dict():
    with open(os.path.join(JWKS_FOLDER, "pubkeys.json")) as key_file:
        return json.load(key_file)


jwks_dict = get_jwks_dict()


def get_ingestion_pem():
    logger.debug(f"JWKS_FOLDER: {JWKS_FOLDER}")
    with open(os.path.join(JWKS_FOLDER, "ingestion.pem"), "rb") as fh:
        return fh.read()


ingestion_pem = get_ingestion_pem()

"""
User object with admin attribute controlled by bluegroup membership.

"""


class AuthenticatedUser:
    def __init__(self, uid: str, is_admin: bool, display_name: str, email: str) -> None:
        self.username = uid
        self.emailAddress = email
        self.admin = is_admin
        self.rname = display_name

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.rname

    @property
    def email(self) -> str:
        return self.emailAddress

    @property
    def uid(self) -> str:
        return self.username

    @property
    def is_admin(self) -> bool:
        return self.admin


no_token_paths = [
    "/api/v1/acp/ping",
    "/api/v1/auth",
    "/api/v1/login",
    "/api/v1/cli_login",
    "/api/v1/cli_auth",
    "/api/v1/docs",
]


class JwtAuthBackend(AuthenticationBackend):
    """
    Expects w3id, IBMiD, or ingestion Bearer token (JWT) in Authorization header.

    Any w3id | IBMiD, or ingestion user can be considered authenticated provided they supply a valid
    token in the authorization header.

    """

    def __init__(self) -> None:
        self.cit = datetime.now(UTC).timestamp()

    async def authenticate_ingestion(self, conn):
        """
        Support a shared public key to validate internal service submissions

        Since it is expected that user tokens will *never* verify against the ingestion
        key, decode errors are logged as debug rather than errors.  I.e. They are EXPECTED.
        This is due to the removal of claims inspection prior to invoking decode with key.
        The removal of the afore mentioned provides an improvment on two points.
        - Token is always verified prior to usage
        - The issuer can be *anything* as long as it decodes against the ingestion KEY.
        """
        logger.debug("-->authenticate_ingestion()")
        if "Authorization" not in conn.headers:
            if conn.url.path in no_token_paths:
                return
            logger.error("Missing Authorization header.")
            return
        auth = conn.headers["Authorization"]
        scheme, credentials = auth.split()
        logger.debug("scheme: %s", scheme)
        if scheme.lower() != "bearer":
            return
        try:
            # header, claims = jwt.verify_jwt(credentials, isg_jwks, ['RS256'],pyjwt_datetime.timedelta(0),True)
            claims = jwt.decode(credentials, ingestion_pem, ["RS256"], None, True)
            return AuthCredentials(["authenticated"]), AuthenticatedUser(
                claims["uid"], False, claims["displayName"], claims["emailAddress"]
            )
        except BaseException as err:
            logger.debug("token failed to verify as an ingestion token %s", str(err))
        # if execution reaches here, the JWT failed to verify against any of the supplied keys (OR, the verified user is not in the bluegroup)
        logger.debug("iterated over all available ingestion keys and jwt verification failed.")
        return None

    async def authenticate(self, conn):
        logger.debug("-->authenticate()")
        if "Authorization" not in conn.headers:
            if conn.url.path in no_token_paths:
                return
            logger.error("Missing Authorization header.")
            return
        auth = conn.headers["Authorization"]
        scheme, credentials = auth.split()
        logger.debug("scheme: %s", scheme)
        if scheme.lower() != "bearer":
            return
        ac_ingestion = await self.authenticate_ingestion(conn)
        if ac_ingestion is not None:
            logger.info("(👁️) - Ingestion token verified OK")
            return ac_ingestion

        for pub_key in jwks_dict["keys"]:
            try:
                # obj_key = jwk.JWK.from_json(json.dumps(pub_key))
                obj_key = jwt.PyJWK(pub_key)
                # explicitly only check exp and iat, nbf (not before time) is not included in w3id
                claims = jwt.decode(credentials, obj_key, ["RS256"], None, True, audience=AUDIENCE)
                logger.debug(json.dumps(claims))
                is_admin = False
                return AuthCredentials(["authenticated"]), AuthenticatedUser(
                    claims["uid"], is_admin, claims["displayName"], claims["emailAddress"]
                )
            except BaseException as err:
                estr = str(err)
                if estr is not None and estr.count("expired") > 0:
                    logger.error(str(err))
                # logger.info('caught an exception %s', str(err))
                continue
        # if execution reaches here, the JWT failed to verify against any of the supplied keys (OR, the verified user is not in the bluegroup)
        logger.info("iterated over all available keys and jwt verification failed.")
        raise AuthenticationError("JWT verification failed")


def on_auth_error(request, exc: Exception):
    return JSONResponse({"error": str(exc)}, status_code=401)
