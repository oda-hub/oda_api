import json
import base64
import logging
from os import environ, getcwd, path
from posixpath import join
from types import FunctionType, ModuleType
from typing import Optional

from jwt.exceptions import ExpiredSignatureError # type: ignore

default_algorithm = 'HS256'

logger = logging.getLogger("oda_api.token")

    
try:
    import jwt
except ImportError:
    jwt = None # type: ignore
    logger.debug("no pyjwt installed: some token operations will not be available")

def format_token(decoded_oda_token: dict):
    return json.dumps(decoded_oda_token, indent=4, sort_keys=True)

## decoding

def decode_oda_token(token: str, secret_key=None, allow_invalid=False):
    if jwt is None:
        logger.info("decoding token without jwt")
        return json.loads(base64.b64decode(token.split(".")[1]+"=").decode())
    else:
        if secret_key is None:
            logger.info("decoding token with jwt and NOT verifying")
            return jwt.decode(token, 
                            "", 
                            algorithms=[default_algorithm],
                            options=dict(
                                verify_signature=False
                            ))
        else:
            logger.info("decoding token with jwt and verifying")
            try:
                return jwt.decode(token, 
                                secret_key, 
                                algorithms=[default_algorithm],
                                options=dict(
                                    verify_signature=True
                                ))
            except ExpiredSignatureError as e:
                logger.warning("token invalid: %s", e)
                if allow_invalid:
                    logger.warning("allowing invalid token")
                    return jwt.decode(token, 
                                    secret_key, 
                                    algorithms=[default_algorithm],
                                    options=dict(
                                        verify_signature=False
                                    ))
                else:
                    raise

def decode_oauth2_token(token: str):
    # usually comes in cookies['_oauth2_proxy']
    return json.loads(base64.b64decode(token.split(".")[0]+"=").decode())

## preserving

def discover_token():
    failed_methods = []
    token = None

    for n, m in [
        ("environment variable ODA_TOKEN", lambda: environ['ODA_TOKEN'].strip()),
        ("file in current directory", lambda: open(
                path.join(getcwd(), ".oda-token")
            ).read().strip()),
        ("file in home", lambda: open(
                path.join(environ["HOME"], ".oda-token")
            ).read().strip()),
    ]:
        try:
            logger.info("searching for token in %s", n)
            token = m()
        except Exception as e:
            failed_methods.append(f"{n}: {e}")
            logger.debug("failed to find token with current method: %s", failed_methods[-1])

    if token is None:
        logger.debug("failed to discover token with any known method")        

    return token

## updating

def update_token(token, secret_key, payload_mutation: FunctionType, allow_invalid=False):
    if secret_key is None:
        raise RuntimeError("unable to update token without valid secret key")
    
    try:
        token_payload = jwt.decode(token, secret_key, algorithms=[default_algorithm]) 
    except ExpiredSignatureError as e:
        logger.warning("provided token is invalid: %s", e)
        if allow_invalid:
            token_payload = jwt.decode(token, secret_key, algorithms=[default_algorithm], options=dict(verify_signature=False)) 
            logger.warning("invalid token payload will be used as requested")
        else:
            raise RuntimeError("refusing to update invalid token")

    mutated_token_payload = payload_mutation(token_payload) 

    out_token = jwt.encode(mutated_token_payload, secret_key, algorithm=default_algorithm)

    return out_token

def update_token_suppress_email(token, secret_key):
    def payload_mutation(token_payload):
        token_payload['mssub'] = False
        token_payload['msdone'] = False
        token_payload['msfail'] = False

    return update_token(token, secret_key, payload_mutation)