import click
import logging

import oda_api.api as api

logger = logging.getLogger('cli')

@click.group()
@click.option("-d", "--debug", is_flag=True)
@click.option("-u", "--dispatcher-url", type=str, default=None)
@click.pass_obj
def cli(obj, debug=False, dispatcher_url=None):
    if debug:
        logging.basicConfig(level="DEBUG")
    else:
        logging.basicConfig(level="INFO")

    obj['dispatcher'] = api.DispatcherAPI(url=dispatcher_url)

    logger.info("created dispatcher: %s", obj['dispatcher'])

    instruments = obj['dispatcher'].get_instruments_list()


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

    

def main():
    cli(obj={})

if __name__ == "__main__":
    main()
