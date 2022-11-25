import json
import base64
import logging
import os
from typing import Union, Tuple
from os import environ, getcwd, path, remove, chmod
from enum import Enum
from types import FunctionType
import time
import traceback

from jwt.exceptions import ExpiredSignatureError # type: ignore

default_algorithm = 'HS256'

logger = logging.getLogger("oda_api.token")


class TokenLocation(Enum):
    ODA_ENV_VAR = "environment variable ODA_TOKEN"
    FILE_CUR_DIR = "file in current directory"
    FILE_HOME = "file in home"

try:
    import jwt
except ImportError:
    jwt = None # type: ignore
    logger.debug("no pyjwt installed: some token operations will not be available")

def format_token(decoded_oda_token: dict):
    return json.dumps(decoded_oda_token, indent=4, sort_keys=True)

## decoding

def decode_oda_token(token: str, secret_key=None, allow_invalid=False) -> dict:
    if token is None:
        raise RuntimeError('provided token is None')

    if jwt is None:
        logger.info("decoding token without jwt")
        return json.loads(base64.b64decode(token.split(".")[1]+"=").decode())
    
    if secret_key is None:
        secret_key = ""
        allow_invalid = True
    
    decode_options = {}

    if allow_invalid:
        decode_options['verify_signature'] = False
        decode_options['verify_exp'] = False

    try:
        return jwt.decode(token, 
                          secret_key, 
                          algorithms=[default_algorithm],
                          options=decode_options)
                
    except ExpiredSignatureError as e:
        logger.warning("problem decoding token: %s", repr(e))
        if allow_invalid:
            raise RuntimeError("expired token despite no verification?")

    except Exception as e:
        traceback.format_exc()
        logger.error(f'unexplained exception in decode token: %s\n%s\n%s', token, repr(e), traceback.format_exc())
        raise

    raise RuntimeError()


def decode_oauth2_token(token: str):
    # usually comes in cookies['_oauth2_proxy']
    return json.loads(base64.b64decode(token.split(".")[0]+"=").decode())


def get_token_roles(decoded_token):
    # extract role(s)
    roles = None
    if 'roles' in decoded_token:
        if isinstance(decoded_token['roles'], str):
            roles = decoded_token['roles'].split(',')
        elif isinstance(decoded_token['roles'], list):
            roles = decoded_token['roles']
        roles = [r.strip() for r in roles]
    return roles


def compare_token(decoded_token1, decoded_token2):
    result = []

    current_time = time.time()
    decoded_token1_expires_in_s = decoded_token1['exp'] - current_time
    decoded_token2_expires_in_s = decoded_token2['exp'] - current_time

    if decoded_token1_expires_in_s > decoded_token2_expires_in_s:
        time_result_code = 1
    elif decoded_token1_expires_in_s < decoded_token2_expires_in_s:
        time_result_code = -1
    else:
        time_result_code = 0
    result.append(time_result_code)

    decoded_token1_roles = get_token_roles(decoded_token1)
    decoded_token2_roles = get_token_roles(decoded_token2)

    token1_roles_difference = set(decoded_token1_roles) - set(decoded_token2_roles)
    token2_roles_difference = set(decoded_token2_roles) - set(decoded_token1_roles)

    if token1_roles_difference != set() and token2_roles_difference == set():
        roles_result_code = 1
    elif len(token1_roles_difference) < len(token2_roles_difference):
        roles_result_code = -1
    elif len(token1_roles_difference) == len(token2_roles_difference) and \
            (token1_roles_difference == set() and token2_roles_difference == set()):
        roles_result_code = 0
    result.append(roles_result_code)

    return result


def rewrite_token(new_token,
                  token_write_methods: Union[Tuple[TokenLocation], TokenLocation] = None,
                  force_rewrite=False
                  ):
    current_token, discover_method = discover_token_and_method(allow_invalid=True)
    if current_token is not None:
        current_decoded_token = decode_oda_token(current_token, allow_invalid=True)
        current_decoded_token_expires_in_s = current_decoded_token['exp'] - time.time()

        new_decoded_token = decode_oda_token(new_token, allow_invalid=True)
        new_decoded_token_expires_in_s = new_decoded_token['exp'] - time.time()

        if new_decoded_token_expires_in_s < current_decoded_token_expires_in_s:
            warning_msg = "The new token will expire before the current one"
            if force_rewrite:
                warning_msg += ", but it will be used"
                logger.warning(warning_msg)
            else:
                raise RuntimeError("Expiration time of the refreshed token is lower than "
                                   "the currently available one, please pass force=True to overwrite")

        current_decoded_token_roles = get_token_roles(current_decoded_token)
        new_decoded_token_roles = get_token_roles(new_decoded_token)
        new_roles_difference = set(new_decoded_token_roles) - set(current_decoded_token_roles)
        current_roles_difference = set(current_decoded_token_roles) - set(new_decoded_token_roles)
        if new_roles_difference != set() and current_roles_difference == set():
            logger.warning("The new token has more roles than the current one:\n"
                           f"roles current token: {current_decoded_token_roles}\n"
                           f"roles new token: {new_decoded_token_roles}")
        elif len(new_decoded_token_roles) < len(current_decoded_token_roles):
            warning_msg = "The new token has less roles than the current one:\n" \
                          f"roles current token: {current_decoded_token_roles}\n" \
                          f"roles new token: {new_decoded_token_roles}\n"
            if force_rewrite:
                warning_msg += ", but it will be used.\n"
                logger.warning(warning_msg)
            else:
                logger.warning(warning_msg)
                raise RuntimeError("The roles of the new token are less than those of the current one,"
                                   " please pass force=True to overwrite")

    if token_write_methods is not None:
        if current_token is not None:
            with open("old-oda-token_" + str(time.time()), 'w') as ft:
                ft.write(current_token)

        if isinstance(token_write_methods, TokenLocation):
            token_write_methods = token_write_methods,

        if discover_method is not None:
            if discover_method == TokenLocation.ODA_ENV_VAR:
                environ.pop('ODA_TOKEN', None)
            elif discover_method == TokenLocation.FILE_CUR_DIR:
                remove(path.join(getcwd(), ".oda-token"))
            elif discover_method == TokenLocation.FILE_HOME:
                remove(path.join(environ["HOME"], ".oda-token"))

        for token_write_method in token_write_methods:
            if token_write_method == TokenLocation.ODA_ENV_VAR:
                environ['ODA_TOKEN'] = new_token
            elif token_write_method == TokenLocation.FILE_CUR_DIR:
                with open(path.join(getcwd(), ".oda-token"), 'w') as ft:
                    ft.write(new_token)
                chmod(path.join(getcwd(), ".oda-token"), 0o400)
            elif token_write_method == TokenLocation.FILE_HOME:
                with open(path.join(environ["HOME"], ".oda-token"), 'w') as ft:
                    ft.write(new_token)
                chmod(path.join(environ["HOME"], ".oda-token"), 0o400)
        # sanity check on the newly written token
        newly_discovered_token = discover_token()
        if newly_discovered_token != new_token:
            raise RuntimeError("Something went wrong when writing the newly created token, "
                               "and this was not properly written")


def discover_token_and_method(
        allow_invalid=False,
        token_discovery_methods=None):
    failed_methods = []
    token = None
    if token_discovery_methods is None:
        token_discovery_methods = *(n.value for n in TokenLocation),
    else:
        token_discovery_methods = TokenLocation[str.upper(token_discovery_methods)].value,

    for n in TokenLocation:
        if n.value in token_discovery_methods:
            try:
                if n == TokenLocation.ODA_ENV_VAR:
                    token = environ['ODA_TOKEN'].strip()
                elif n == TokenLocation.FILE_CUR_DIR:
                    with open(path.join(getcwd(), ".oda-token")) as ft:
                        token = ft.read().strip()
                elif n == TokenLocation.FILE_HOME:
                    with open(path.join(environ["HOME"], ".oda-token")) as ft:
                        token = ft.read().strip()

                logger.debug("searching for token in %s", n)
                decoded_token = decode_oda_token(token, allow_invalid=allow_invalid)

                expires_in_s = decoded_token['exp'] - time.time()

                if expires_in_s < 0:
                    logger.debug("token expired %.1f h ago!", -expires_in_s / 3600)
                    if allow_invalid:
                        break
                    else:
                        token = None
                else:
                    logger.info("found token in %s your token payload: %s", n, format_token(decoded_token))
                    logger.info("token expires in %.1f h", expires_in_s / 3600)
                    break
            except Exception as e:
                failed_methods.append(f"{n}: {e}")
                logger.debug("failed to find token with current method: %s", failed_methods[-1])
                token = None

    if token is None:
        logger.debug("failed to discover token with any known method")
    else:
        logger.debug("discovered token method %s", n)

    return token, n


#TODO: move to dynaconf
def discover_token(
        allow_invalid=False,
        token_discovery_methods=None):
    token, discovery_method = discover_token_and_method(
        allow_invalid=allow_invalid,
        token_discovery_methods=token_discovery_methods
    )
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
            token_payload = jwt.decode(token, secret_key, algorithms=[default_algorithm], options=dict(verify_signature=False, verify_exp=False)) 
            logger.warning("invalid token payload will be used as requested")
        else:
            raise RuntimeError("refusing to update invalid token")

    mutated_token_payload = payload_mutation(token_payload) 

    out_token = jwt.encode(mutated_token_payload, secret_key, algorithm=default_algorithm)

    return out_token