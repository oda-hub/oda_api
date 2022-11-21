from flask.json import JSONEncoder
import logging
import numpy as np

from .data_products import NumpyDataProduct, ODAAstropyTable, PictureProduct, BinaryData

from astropy.io.fits.card import Undefined as astropyUndefined

class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return list(obj)

        if isinstance(obj, astropyUndefined):
            return "UNDEFINED"
        
        if isinstance(obj, (NumpyDataProduct, ODAAstropyTable, PictureProduct)):
            return obj.encode()
        
        if isinstance(obj, BinaryData):
            return obj.encode()[0].decode() 
            # NOTE: in current implementation of BinaryData md5sum is anyway not used in decoding, so ignored here
        
        if isinstance(obj, bytes):
            return obj.decode()

        logging.error("problem encoding %s, will NOT send as string", obj) # TODO: dangerous probably, fix!
        raise RuntimeError('unencodable ' + str(obj))

        #return JSONEncoder.default(self, obj) # TODO: do we really don't want to encode other objects?