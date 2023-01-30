from datetime import datetime
from email.policy import default
import json
from attr import validate
from black import out
import click
import logging
import time

import oda_api.api as api
from oda_api import plot_tools
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
@click.option("-T", "--discover-token", "_discover_token", is_flag=True)
@click.pass_obj
def get(obj, instrument, product, argument, _discover_token):
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

            if _discover_token:
                request['token'] = discover_token()
                
            product = obj['dispatcher'].get_product(**request)

            logger.info("got product: %s", product.as_list())

            for p in product._p_list:
                logger.info("> %s", p)
                for du in p.data_unit:
                    logger.info(">> %s", du.data)

            for k, v in plot_tools.__dict__.items():
                if k.startswith('Oda'):
                    try:
                        O = v(product)
                        logger.info('%s can be parsed as %s => %s', product, v, O)
                        fn = O.get_image_for_gallery()
                        logger.info("plotted as %s", fn)
                    except Exception as e:
                        logger.info('failed to parse %s as %s (%s), %s', product, k, v, repr(e))


@cli.group("token")
@click.option("-s", "--secret", default=None)
@click.option('--allow-invalid', is_flag=True, default=False)
@click.pass_obj
def tokencli(obj, secret, allow_invalid):
    obj['secret_key'] = secret
    obj['allow_invalid'] = allow_invalid
    obj['token'] = discover_token(allow_invalid=allow_invalid)
    obj['decoded_token'] = decode_oda_token(
                                obj['token'], 
                                secret_key=obj['secret_key'], 
                                allow_invalid=obj['allow_invalid'])
                            



@tokencli.command()
@click.pass_obj
def inspect(obj):

    decoded_token = obj['decoded_token']

    logger.info("your token payload: %s", format_token(decoded_token))

    expires_in_s = decoded_token['exp'] - time.time()

    if expires_in_s < 0:
        logger.warning("token expired %.1f h ago!", -expires_in_s/3600)    
    else:
        logger.info("expires in %.1f h", expires_in_s/3600)

    
@tokencli.command()
@click.option("--disable-email", default=False, is_flag=True)
@click.option("--new-validity-hours", default=None, type=float)
@click.pass_obj
def modify(obj, disable_email, new_validity_hours):
    token = obj['token']
    decoded_token = obj['decoded_token']

    logger.info("your current token payload: %s", format_token(decoded_token))

    def mutate_token_payload(payload): 
        new_payload = payload.copy()
        if disable_email:
            logger.info("disabling email submission")
            new_payload['mssub'] = False
            new_payload['msdone'] = False
            # TODO: think if need this
            # new_payload['msfail'] = False


        if new_validity_hours is not None:
            new_payload['exp'] = time.time() + new_validity_hours * 3600
            logger.info("updating validity to %s h from now, until %s", new_validity_hours, time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(new_payload['exp'])))

        return new_payload

    updated_token = update_token(token, secret_key=obj['secret_key'], payload_mutation=mutate_token_payload, allow_invalid=obj['allow_invalid'])    
    decoded_token = decode_oda_token(updated_token, secret_key=obj['secret_key'], allow_invalid=True)

    logger.info("your new token payload: %s", repr(format_token(decoded_token)))
    logger.info("your new token (secret!): %s", updated_token.decode() if isinstance(updated_token, bytes) else updated_token)


@cli.command("inspect")
@click.option("-s", "--store", default="dispatcher-state.json")
@click.option("-j", "--job-id", default=None)
@click.option("-l", "--local", default=False, is_flag=True)
# @click.option("-V", "--validate", default=None)
@click.pass_obj
def inspect_state(obj, store, job_id, local):
    if local:
        state = json.load(open(store))
    else:
        state = obj['dispatcher'].inspect_state(job_id=job_id)    
        json.dump(
                state,
                open(store, "w"),
                indent=4,
                sort_keys=True,
            )

    # if validate:
    for record in sorted(state['records'], key=lambda r:r['mtime']):
        print("session_id", record['session_id'], "job_id", record['job_id'], datetime.fromtimestamp(record['mtime']))
        for email in record.get('analysis_parameters', {}).get('email_history', []):
            print("    - ", email)


def main():
    cli(obj={})

if __name__ == "__main__":
    main()
