import click
import logging
import time

import oda_api.api as api
from oda_api.token import discover_token, decode_oda_token, format_token, update_token

logger = logging.getLogger('oda_api')

@click.group()
@click.option("-d", "--debug", is_flag=True)
@click.option("-u", "--dispatcher-url", type=str, default=None)
@click.option("-t", "--test-connection", is_flag=True, default=False)
@click.option("-w/-nw", "--wait/--no-wait", default=True)
@click.pass_obj
def cli(obj, debug=False, dispatcher_url=None, test_connection=False, wait=True):
    if debug:
        logging.basicConfig(level="DEBUG")
        logging.getLogger('oda_api').setLevel("DEBUG")
    else:
        logging.basicConfig(level="INFO")
        logging.getLogger('oda_api').setLevel("INFO")

    obj['dispatcher'] = api.DispatcherAPI(url=dispatcher_url, wait=wait)

    logger.info("created dispatcher: %s", obj['dispatcher'])

    if test_connection:
        instruments = obj['dispatcher'].get_instruments_list()
        logger.info("dispatcher has instruments: %s", list([i for i in instruments]))


@cli.command()
@click.option("-i", "--instrument", default=None)
@click.option("-p", "--product", default=None)
@click.option("-a", "--argument", default=None, multiple=True)
@click.pass_obj
def get(obj, instrument, product, argument):
    if instrument is None:
        logger.info("found instruments: %s", obj['dispatcher'].get_instruments_list())
    else:
        if product is None:
            logger.info("instrument description: %s",
                        obj['dispatcher'].get_instrument_description(instrument))
        else:
            request = {
                        'instrument': instrument,
                        'product': product,
                        **{
                            l.split("=", 1)[0]:l.split("=", 1)[1]
                            for l in argument
                        }
                      }

            logger.debug("request to dispatcher %s", request)

            product = obj['dispatcher'].get_product(**request)

            logger.info("got product: %s", product.as_list())

            for p in product._p_list:
                logger.info("> %s", p)
                for du in p.data_unit:
                    logger.info(">> %s", du.data)


@cli.group("token")
@click.option("-s", "--secret", default=None)
@click.pass_obj
def tokencli(obj, secret):
    obj['secret_key'] = secret

@tokencli.command()
@click.pass_obj
def inspect(obj):
    token = discover_token()

    if token is None:
        logger.warn("no token found!")
        return

    decoded_token = decode_oda_token(token, secret_key=obj['secret_key'])

    logger.info("your token payload: %s", format_token(decoded_token))

    expires_in_s = decoded_token['exp'] - time.time()

    if expires_in_s < 0:
        logger.warning("token expired %.1f h ago!", -expires_in_s/3600)    
    else:
        logger.info("expires in %.1f h", expires_in_s/3600)

    
@tokencli.command()
@click.option("--disable-email", default=False, is_flag=True)
@click.option("--allow-invalid", default=False, is_flag=True)
@click.option("--new-validity-hours", default=None, type=float)
@click.pass_obj
def modify(obj, disable_email, allow_invalid, new_validity_hours):
    token = discover_token()

    decoded_token = decode_oda_token(token, secret_key=obj['secret_key'], allow_invalid=allow_invalid)

    logger.info("your current token payload: %s", format_token(decoded_token))

    def mutate_token_payload(payload):
        new_payload = payload.copy()
        if disable_email:
            logger.info("disabling email submission")
            new_payload['mssub'] = False
            new_payload['msdone'] = False

        if new_validity_hours is not None:
            new_payload['exp'] = time.time() + new_validity_hours * 3600
            logger.info("updating validity to %s h from now, until %s", new_validity_hours, time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(new_payload['exp'])))

        return new_payload

    updated_token = update_token(token, secret_key=obj['secret_key'], payload_mutation=mutate_token_payload, allow_invalid=allow_invalid)
    decoded_token = decode_oda_token(updated_token, secret_key=obj['secret_key'], allow_invalid=allow_invalid)

    logger.info("your new token payload: %s", format_token(decoded_token))
    logger.info("your new token (secret!): %s", updated_token.decode() if isinstance(updated_token, bytes) else updated_token)


def main():
    cli(obj={})

if __name__ == "__main__":
    main()
