import oda_api
import json
import base64
import logging
from os import environ, getcwd, path
from posixpath import join
from types import FunctionType
import time

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

#TODO: move to dynaconf
def discover_token(token_discovery_methods=(
        "environment variable ODA_TOKEN",
        "file in current directory",
        "file in home")):
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
        if n in token_discovery_methods:
            try:
                logger.debug("searching for token in %s", n)
                token = m()
                decoded_token = oda_api.token.decode_oda_token(token)            

                expires_in_s = decoded_token['exp'] - time.time()

                if expires_in_s < 0:
                    logger.debug("token expired %.1f h ago!", -expires_in_s/3600)    
                    token = None
                else:
                    logger.info("found token in %s your token payload: %s", n, format_token(decoded_token))
                    logger.info("token expires in %.1f h", expires_in_s/3600)                
                    break
            except Exception as e:
                failed_methods.append(f"{n}: {e}")
                logger.debug("failed to find token with current method: %s", failed_methods[-1])
                token = None

    if token is None:
        logger.debug("failed to discover token with any known method")        
    else:
        logger.debug("discovered token method %s", n)        

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