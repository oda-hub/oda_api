import click
import logging

import oda_api.api as api
from oda_api.token import discover_token, decode_oda_token, format_token, update_token

logger = logging.getLogger('oda_api')

@click.group()
@click.option("-d", "--debug", is_flag=True)
@click.option("-u", "--dispatcher-url", type=str, default=None)
@click.pass_obj
def cli(obj, debug=False, dispatcher_url=None):
    if debug:
        logging.basicConfig(level="DEBUG")
        logging.getLogger('oda_api').setLevel("DEBUG")
    else:
        logging.basicConfig(level="INFO")
        logging.getLogger('oda_api').setLevel("INFO")

    obj['dispatcher'] = api.DispatcherAPI(url=dispatcher_url)

    logger.info("created dispatcher: %s", obj['dispatcher'])

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

    decoded_token = decode_oda_token(token, secret_key=obj['secret_key'])

    logger.info("your token: %s", format_token(decoded_token))

    
@tokencli.command()
@click.option("--disable-email", default=False)
@click.pass_obj
def update(obj, disable_email):
    token = discover_token()

    decoded_token = decode_oda_token(token, secret_key=obj['secret_key'])

    logger.info("your current token payload: %s", format_token(decoded_token))

    def mutate_token_payload(payload):
        return payload

    updated_token = update_token(token, secret_key=obj['secret_key'])

    logger.info("your new current token: %s", format_token(decoded_token))


def main():
    cli(obj={})

if __name__ == "__main__":
    main()
