import pytest

def test_remote_301_post():
    import logging

    logging.basicConfig(level="DEBUG")

    from oda_api.api import DispatcherAPI, URLRedirected
    from oda_api.token import discover_token

    api_cat_str = '{"cat_frame": "fk5", "cat_coord_units": "deg", "cat_column_list": [[17, 87], ["GRS 1915+105", "MAXI J1820+070"], [29.396455764770508, 1803.1607666015625], [288.799560546875, 275.0911865234375], [10.939922332763672, 7.185144901275635], [-32768, -32768], [2, 2], [0, 0], [0.0002800000074785203, 0.00041666667675599456]], "cat_column_names": ["meta_ID", "src_names", "significance", "ra", "dec", "NEW_SOURCE", "ISGRI_FLAG", "FLAG", "ERR_RAD"], "cat_column_descr": [["meta_ID", "<i8"], ["src_names", "<U20"], ["significance", "<f8"], ["ra", "<f8"], ["dec", "<f8"], ["NEW_SOURCE", "<i8"], ["ISGRI_FLAG", "<i8"], ["FLAG", "<i8"], ["ERR_RAD", "|O"]], "cat_lat_name": "dec", "cat_lon_name": "ra"}'
    
    with pytest.raises(URLRedirected) as execinfo:
        disp = DispatcherAPI(url="http://www.astro.unige.ch/mmoda/dispatch-data")
        spectrum = disp.get_product(
            instrument="isgri",
            product="isgri_spectrum",
            product_type="Real",
            osa_version="OSA11.1",
            RA="275.09142677",
            DEC="7.18535523",
            radius="8",
            T1="58193.455",
            T2="58246.892",
            T_format="mjd",
            max_pointings="50",
            token=discover_token(),
            selected_catalog=api_cat_str,
        )

    assert execinfo.value.args[0] == ('the service was moved permanently, please reinitialize DispatcherAPI '
                                      'with "https://www.astro.unige.ch/mmoda/dispatch-data/run_analysis" '
                                      '(you asked for "http://www.astro.unige.ch/mmoda/dispatch-data/run_analysis")')