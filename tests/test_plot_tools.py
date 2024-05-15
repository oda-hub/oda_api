import pathlib
import pytest


@pytest.mark.live
def test_plot_tools_notebook(request, remove_any_token_from_environment):
    import papermill as pm

    in_nb = pathlib.Path(request.fspath.dirname) / "../doc/source/user_guide/Show_and_Save_Products.ipynb"

    # TODO: can monkey-patch here

    pm.execute_notebook(
        in_nb,
        "output.ipynb",
        parameters=dict(),
        log_level="DEBUG",
        log_output=True
    )

@pytest.mark.xfail(reason="fails")
def test_image_no_sources():
    from astropy.wcs import WCS
    from oda_api.plot_tools import OdaImage

    oda_image = OdaImage(None)
    try:
        oda_image.build_fig(header=WCS().to_header(),
                            meta={"src_name": "testsource"},
                            sources=[])
        assert False, 'the code above should have raised the ValueError exception'
    except ValueError:
        pass

def test_lc_adjustend_bins(request):
    import numpy as np
    from oda_api.plot_tools import OdaLightCurve
    from oda_api.api import NumpyDataProduct, DataCollection
    from astropy.table import Table

    lc_fn = pathlib.Path(request.fspath.dirname) / "test_data/lc.fits"

    lc_data = Table.read(lc_fn)

    t = lc_data['TIME']
    i = np.argmin(t[1:]-t[:-1])
    print(lc_data[i:i+2])

    # both bins have the same timestamp
    assert lc_data[i:i+2]['TIME'].std() < 1e-10

    # two parts of the same bin
    assert lc_data[i:i+2]['FRACEXP'].sum() <= 1 
    
    oda_lc = OdaLightCurve(DataCollection([
        NumpyDataProduct.from_fits_file(lc_fn, meta_data={"src_name": "test_source"})
    ]))

    oda_lc.build_fig()    