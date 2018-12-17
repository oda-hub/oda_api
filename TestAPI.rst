
.. code:: ipython2

    from oda_api.api import DispatcherAPI
    from oda_api.plot_tools import OdaImage,OdaLightCurve
    from oda_api.data_products import BinaryData
    import os
    %matplotlib notebook


### build the dispatcher object

.. code:: ipython2

    #external axcess
    #cookies=dict(_oauth2_proxy=open(os.environ.get('HOME')+'/.oda-api-token').read().strip())
    #disp=DispatcherAPI(host='analyse-staging-1.1.reproducible.online/dispatch-data',instrument='mock',cookies=cookies,protocol='https')
    
    #internal
    disp=DispatcherAPI(host='cdcicn01.isdc.unige.ch:32003/dispatch-data',instrument='mock')
    
    #cdicweb01
    #disp=DispatcherAPI(host='10.194.169.161',port=32784,instrument='mock')
    
    #local
    #disp=DispatcherAPI(host='0.0.0.0',port=5000,instrument='mock')
     

.. code:: ipython2

    instr_list=disp.get_instruments_list()
    for i in instr_list:
        print (i)


.. parsed-literal::

    isgri
    jemx
    polar


get the description of the instrument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    disp.get_instrument_description('isgri')


.. parsed-literal::

    
    --------------
    instrumet: isgri
    
    --------------
    query_name: src_query
     name: src_name,  value: test,  units: str, 
     name: RA,  value: 0.0,  units: deg, 
     name: DEC,  value: 0.0,  units: deg, 
     name: T1,  value: 2001-12-11T00:00:00.000,  units: None, 
     name: T2,  value: 2001-12-11T00:00:00.000,  units: None, 
    
    --------------
    query_name: isgri_parameters
     name: user_catalog,  value: None,  units: str, 
     name: scw_list,  value: [],  units: names_list, 
     name: radius,  value: 5.0,  units: deg, 
     name: max_pointings,  value: 50,  units: None, 
     name: E1_keV,  value: 10.0,  units: keV, 
     name: E2_keV,  value: 40.0,  units: keV, 
     name: osa_version,  value: None,  units: str, 
    
    --------------
    query_name: isgri_image_query
     product_name: isgri_image
     name: detection_threshold,  value: 0.0,  units: sigma, 
     name: image_scale_min,  value: None,  units: None, 
     name: image_scale_max,  value: None,  units: None, 
    
    --------------
    query_name: isgri_spectrum_query
     product_name: isgri_spectrum
    
    --------------
    query_name: isgri_lc_query
     product_name: isgri_lc
     name: time_bin,  value: 1000.0,  units: sec, 
    
    --------------
    query_name: spectral_fit_query
     product_name: spectral_fit
     name: xspec_model,  value: powerlaw,  units: str, 
     name: ph_file_name,  value: ,  units: str, 
     name: arf_file_name,  value: ,  units: str, 
     name: rmf_file_name,  value: ,  units: str, 


get the description of the product
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    disp.get_product_description(instrument='isgri',product_name='isgri_image')


.. parsed-literal::

    --------------
    parameters for  product isgri_image and instrument isgri
    
    --------------
    instrumet: isgri
    
    --------------
    query_name: src_query
     name: src_name,  value: test,  units: str, 
     name: RA,  value: 0.0,  units: deg, 
     name: DEC,  value: 0.0,  units: deg, 
     name: T1,  value: 2001-12-11T00:00:00.000,  units: None, 
     name: T2,  value: 2001-12-11T00:00:00.000,  units: None, 
    
    --------------
    query_name: isgri_parameters
     name: user_catalog,  value: None,  units: str, 
     name: scw_list,  value: [],  units: names_list, 
     name: radius,  value: 5.0,  units: deg, 
     name: max_pointings,  value: 50,  units: None, 
     name: E1_keV,  value: 10.0,  units: keV, 
     name: E2_keV,  value: 40.0,  units: keV, 
     name: osa_version,  value: None,  units: str, 
    
    --------------
    query_name: isgri_image_query
     product_name: isgri_image
     name: detection_threshold,  value: 0.0,  units: sigma, 
     name: image_scale_min,  value: None,  units: None, 
     name: image_scale_max,  value: None,  units: None, 


check query before submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

we pass 'dry\_run' to check if the request is correct without actually
submitting it

.. code:: ipython2

    data=disp.get_product(instrument='isgri',
                          product='isgri_image',
                          T1='2003-03-15T23:27:40.0',
                          T2='2003-03-16T00:03:12.0',
                          osa_version='OSA10.2',
                          RA='a',
                          DEC=-37.844167,
                          detection_threshold=5.0,
                          radius=15.,
                          product_type='Real',
                          dry_run=True)


.. parsed-literal::

    waiting for remote response, please wait run_analysis http://cdcicn01.isdc.unige.ch:32003/dispatch-data
    
    
    query failed!
    Remote server message:-> failed: setting form parameters
    Remote server error_message-> ValueError(u"Invalid character at col 0 in angle u'a'",)
    Remote server debug_message-> 


::


    ---------------------------------------------------------------------------

    RemoteException                           Traceback (most recent call last)

    <ipython-input-6-fbb1c3c7c2ac> in <module>()
          9                       radius=15.,
         10                       product_type='Real',
    ---> 11                       dry_run=True)
    

    /home/ferrigno/Soft/cdci_api_plugin/oda_api/api.pyc in get_product(self, product, instrument, verbose, dry_run, product_type, **kwargs)
        217         kwargs['dry_run'] = dry_run,
        218 
    --> 219         res = self.request(kwargs)
        220         data = None
        221 


    /home/ferrigno/Soft/cdci_api_plugin/oda_api/api.pyc in request(self, parameters_dict, handle, url)
        110         else:
        111 
    --> 112             raise RemoteException(debug_message=res.json()['exit_status']['error_message'])
        113 
        114 


    RemoteException: Remote analysis exception


get the product
~~~~~~~~~~~~~~~

now we skip the dry\_run to actually get the products

.. code:: ipython2

    data=disp.get_product(instrument='isgri',
                          product='isgri_image',
                          T1='2003-03-15T23:27:40.0',
                          T2='2003-03-16T00:03:15.0',
                          E1_keV=20.0,
                          E2_keV=40.0,
                          osa_version='OSA10.2',
                          RA=255.986542,
                          DEC=-37.844167,
                          detection_threshold=5.0,
                          radius=15.,
                          product_type='Real')


.. parsed-literal::

    waiting for remote response, please wait run_analysis http://cdcicn01.isdc.unige.ch:32003/dispatch-data
    
    
    query done succesfully!


the ODA data structure
~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    data=data[0]
    data.show()


.. parsed-literal::

    ------------------------------
    name: mosaic_image
    meta_data ['src_name', 'instrument', 'product', 'query_parameters']
    number of data units 1
    ------------------------------
    data uniti 0 ,name: ISGR-MOSA-IMA


.. code:: ipython2

    data.show_meta()


.. parsed-literal::

    ------------------------------
    src_name : 
    instrument : isgri
    product : mosaic
    query_parameters : [{"query_name": "isgri_image_query"}, {"product_name": "isgri_image_query"}, {"units": "sigma", "name": "detection_threshold", "value": "5.0"}, {"units": null, "name": "image_scale_min", "value": null}, {"units": null, "name": "image_scale_max", "value": null}]
    ------------------------------


.. code:: ipython2

    data.data_unit[0].data




.. parsed-literal::

    array([[0., 0., 0., ..., 0., 0., 0.],
           [0., 0., 0., ..., 0., 0., 0.],
           [0., 0., 0., ..., 0., 0., 0.],
           ...,
           [0., 0., 0., ..., 0., 0., 0.],
           [0., 0., 0., ..., 0., 0., 0.],
           [0., 0., 0., ..., 0., 0., 0.]], dtype=float32)



.. code:: ipython2

    hdu=data.to_fits_hdu_list()

.. code:: ipython2

    data.data_unit[0].data.shape




.. parsed-literal::

    (455, 455)



.. code:: ipython2

    data.write_fits_file('test.fits',overwrite=True)

the ODA Image plotting tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    %matplotlib notebook
    im=OdaImage(data)

.. code:: ipython2

    im.show()



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <div id='ad7b64c8-1695-4a9c-ab29-1ff3ca14c254'></div>


.. code:: ipython2

    data.data_unit[0].header




.. parsed-literal::

    {u'BASETYPE': u'DAL_ARRAY',
     u'BITPIX': -32,
     u'BSCALE': 1,
     u'BUNIT': u'no units',
     u'BZERO': 0,
     u'CD1_1': -0.0822862539155913,
     u'CD1_2': 0.0,
     u'CD2_1': 0.0,
     u'CD2_2': 0.0822862539155913,
     u'CHANMAX': 40,
     u'CHANMIN': 20,
     u'CHANTYPE': u'PI',
     u'CHECKSUM': u'gESDiCPCgCPCgCPC',
     u'COMMENT': u'STAMP :',
     u'CONFIGUR': u'latest_osa_sw_2015-11-10T03:50:02',
     u'CREATOR': u'ii_skyimage 5.4.4',
     u'CRPIX1': 228.0,
     u'CRPIX2': 228.0,
     u'CRVAL1': 252.939376831055,
     u'CRVAL2': -32.649772644043,
     u'CTYPE1': u'RA---TAN',
     u'CTYPE2': u'DEC--TAN',
     u'CUNIT1': u'deg',
     u'CUNIT2': u'deg',
     u'DATASUM': u'3562348081',
     u'DATE': u'2018-12-14T10:42:40',
     u'DATE-END': u'2003-03-15T23:57:39',
     u'DATE-OBS': u'2003-03-15T23:27:53',
     u'DEADC': 0.775885283090927,
     u'DETNAM': u'ISGRI',
     u'EQUINOX': 2000.0,
     u'EXTNAME': u'ISGR-MOSA-IMA',
     u'EXTREL': u'7.4',
     u'EXTVER': 3,
     u'E_MAX': 40.0,
     u'E_MEAN': 30.0,
     u'E_MIN': 20.0,
     u'GCOUNT': 1,
     u'GRPID1': 1,
     u'HDUCLAS1': u'IMAGE',
     u'HDUCLASS': u'OGIP',
     u'HDUDOC': u'ISDC-IBIS ICD',
     u'HDUVERS': u'1.1.0',
     u'IMATYPE': u'SIGNIFICANCE',
     u'INSTRUME': u'IBIS',
     u'ISDCLEVL': u'IMA',
     u'LATPOLE': 0,
     u'LONGPOLE': 180,
     u'MJDREF': 51544.0,
     u'MOSASPR': 1,
     u'NAXIS': 2,
     u'NAXIS1': 455,
     u'NAXIS2': 455,
     u'OGID': u'String',
     u'ONTIME': 1587.05859375,
     u'ORIGIN': u'ISDC',
     u'PCOUNT': 0,
     u'RADECSYS': u'FK5',
     u'STAMP': u'2018-12-14T10:42:40 ii_skyimage 5.4.4',
     u'TELAPSE': 1589.0,
     u'TELESCOP': u'INTEGRAL',
     u'TFIRST': 1169.97884473118,
     u'TIMEREF': u'LOCAL',
     u'TIMESYS': u'TT',
     u'TIMEUNIT': u'd',
     u'TLAST': 1169.99724526505,
     u'TSTART': 1169.97844975867,
     u'TSTOP': 1169.99912106495,
     u'XTENSION': u'IMAGE'}



the ODA LC plotting tool
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    data=disp.get_product(instrument='isgri',
                          product='isgri_lc',
                          T1='2003-03-15T23:27:40.0',
                          T2='2003-03-16T00:03:12.0',
                          time_bin=70,
                          query_type='Real',
                          osa_version='OSA10.2',
                          RA=255.986542,
                          DEC=-37.844167,
                          detection_threshold=5.0,
                          radius=15.,
                          product_type='Real')


.. parsed-literal::

    waiting for remote response, please wait run_analysis http://cdcicn01.isdc.unige.ch:32003/dispatch-data
    
    
    query done succesfully!


.. code:: ipython2

    d=data[5]

.. code:: ipython2

    d.meta_data




.. parsed-literal::

    {'rate': 'RATE',
     'rate_err': 'ERROR',
     'src_name': 'IGR J17586-2129',
     'time': 'TIME',
     'time_bin': 0.000810143479094966}



.. code:: ipython2

    for s in data:
        print (s.meta_data)


.. parsed-literal::

    {'src_name': 'GX 349+2', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17285-2922', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'AX J1700.2-4220', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17507-2856', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17508-3219', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17586-2129', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'OAO 1657-415', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'GRO J1719-24', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': '4U 1735-444', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17326-3445', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': '4U 1722-30', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17099-2418', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'NEW_6', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'NEW_4', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'NEW_5', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'NEW_2', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'NEW_3', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'NEW_1', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J16248-4603', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17091-3624', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17191-2821', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17103-3341', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'GRS 1747-312', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'GX 354-0', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'IGR J17314-2854', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'GX 1+4', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': 'H 1705-440', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': '1RXS J174607.8-21333', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': '4U 1700-377', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}
    {'src_name': '1E 1740.7-2942', 'rate': 'RATE', 'time_bin': 0.000810143479094966, 'rate_err': 'ERROR', 'time': 'TIME'}


.. code:: ipython2

    lc=data[0]
    lc.data_unit[1].data




.. parsed-literal::

    array([(1169.97924981, 198.35461, 437.45297 , 2.560371 , 16.756752 , 6.457998 , 0.9999995),
           (1169.98006   , 193.66727, 126.646324, 2.4612792, 26.851568 , 6.381221 , 0.9999995),
           (1169.98087017, 165.48798, 106.67175 , 2.2341907, 30.112095 , 5.7995043, 0.9999995),
           (1169.98168037, 170.36319, 110.04073 , 2.2748673, 24.547153 , 5.9050727, 0.9999995),
           (1169.98249057, 179.08556, 114.907425, 2.319844 , 19.534487 , 6.0552273, 0.9999995),
           (1169.98330074, 170.404  , 113.80614 , 2.2976866, 35.34908  , 5.917109 , 0.9999995),
           (1169.98411092, 177.87416, 112.59515 , 2.3153915, 46.75426  , 6.0594788, 0.9999995),
           (1169.98492112, 170.02942, 107.77012 , 2.3239565, 44.09943  , 5.904361 , 0.9999995),
           (1169.9857313 , 169.3733 , 108.96758 , 2.294586 , 38.917126 , 5.8867855, 0.9999995),
           (1169.98654149, 164.62074, 105.818214, 2.196995 , 41.819798 , 5.79285  , 0.9999995),
           (1169.98735168, 160.1174 , 100.87292 , 2.2091596, 19.254423 , 5.7093225, 0.9999995),
           (1169.98816182, 155.62761,  96.28564 , 2.1253731, 27.0208   , 5.6491156, 0.9980645),
           (1169.98897204, 157.76117,  99.53124 , 2.1842995,  5.4414988, 5.689717 , 0.9999995),
           (1169.98978224, 160.51135, 101.27726 , 2.2166016, 24.804337 , 5.76037  , 0.9999995),
           (1169.9905924 , 202.97316, 134.32904 , 2.508761 , 12.959747 , 6.5388417, 0.9987744),
           (1169.9914026 , 186.44695, 121.30305 , 2.4868033, 19.698153 , 6.3498526, 0.9656138),
           (1169.99221276, 174.3811 , 113.04454 , 2.3120182, 17.881779 , 6.0166554, 0.9999995),
           (1169.99302296, 165.1697 , 104.734985, 2.2342746, 16.395714 , 5.8019214, 0.9999995),
           (1169.99383313, 162.44868, 102.406204, 2.2399845, 20.798388 , 5.7825265, 0.9999995),
           (1169.99464334, 161.5848 , 103.45639 , 2.2202725, 25.759254 , 5.7537603, 0.9983044),
           (1169.99545352, 161.81468, 102.12336 , 2.1989408, 13.644187 , 5.7544456, 0.9999995),
           (1169.99626372, 163.90817, 103.48788 , 2.1763616, 22.161682 , 5.7832775, 0.9999995),
           (1169.99695709, 166.75832,  99.20768 , 2.6200924, 17.814016 , 6.9220653, 0.9999995)],
          dtype=(numpy.record, [('TIME', '>f8'), ('TOT_COUNTS', '>f4'), ('BACKV', '>f4'), ('BACKE', '>f4'), ('RATE', '>f4'), ('ERROR', '>f4'), ('FRACEXP', '>f4')]))



.. code:: ipython2

    lc.show()


.. parsed-literal::

    ------------------------------
    name: isgri_lc
    meta_data ['src_name', 'rate', 'time_bin', 'rate_err', 'time']
    number of data units 2
    ------------------------------
    data uniti 0 ,name: PRIMARY
    data uniti 1 ,name: ISGR-SRC.-LCR


.. code:: ipython2

    lc.meta_data




.. parsed-literal::

    {'rate': 'RATE',
     'rate_err': 'ERROR',
     'src_name': 'GX 349+2',
     'time': 'TIME',
     'time_bin': 0.000810143479094966}



.. code:: ipython2

    OdaLightCurve(lc).show(unit_ID=1)



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <div id='d8410402-d151-4ede-a7a9-d88113139b34'></div>


.. code:: ipython2

    lc.data_unit[0].header




.. parsed-literal::

    {u'BITPIX': 8, u'EXTEND': True, u'NAXIS': 0, u'SIMPLE': True}



Polar LC
~~~~~~~~

.. code:: ipython2

    #conda create --name=polar_root root=5 python=3 -c nlesc
    #source activate poloar_root
    #conda install astropy future -c nlesc
    #conda install -c conda-forge json_tricks
    #from oda_api.api import DispatcherAPI
    #from oda_api.data_products import BinaryData
    #from oda_api.plot_tools import OdaImage,OdaLightCurve
    #disp=DispatcherAPI(host='10.194.169.161',port=32784,instrument='mock',protocol='http')
    data=disp.get_product(instrument='polar',product='polar_lc',T1='2016-12-18T08:32:21.000',T2='2016-12-18T08:34:01.000',time_bin=0.5,verbose=True,dry_run=False)


.. parsed-literal::

    waiting for remote response, please wait run_analysis http://cdcicn01.isdc.unige.ch:32003/dispatch-data
    
    
    query done succesfully!


.. code:: ipython2

    lc=data[0]
    root=data[1]
    open('lc.root', "wb").write(root)

.. code:: ipython2

     open('lc.root', "wb").write(root)

.. code:: ipython2

    OdaLightCurve(lc).show(unit_ID=0)



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <div id='c42963c8-919d-4fec-8cda-0b61f7770935'></div>


the ODA and spectra
~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    data=disp.get_product(instrument='isgri',
                          product='isgri_spectrum',
                          T1='2003-03-15T23:27:40.0',
                          T2='2003-03-16T00:03:12.0',
                          time_bin=50,
                          query_type='Real',
                          osa_version='OSA10.2',
                          RA=255.986542,
                          DEC=-37.844167,
                          detection_threshold=5.0,
                          radius=15.,
                          product_type='Real' )


.. parsed-literal::

    waiting for remote response, please wait run_analysis http://cdcicn01.isdc.unige.ch:32003/dispatch-data
    
    
    query done succesfully!


.. code:: ipython2

    for ID,s in enumerate(data):
        print (ID,s.meta_data)


.. parsed-literal::

    (0, {'src_name': 'GX 349+2', 'product': 'isgri_spectrum'})
    (1, {'src_name': 'GX 349+2', 'product': 'isgri_arf'})
    (2, {'src_name': 'GX 349+2', 'product': 'isgri_rmf'})
    (3, {'src_name': 'IGR J17285-2922', 'product': 'isgri_spectrum'})
    (4, {'src_name': 'IGR J17285-2922', 'product': 'isgri_arf'})
    (5, {'src_name': 'IGR J17285-2922', 'product': 'isgri_rmf'})
    (6, {'src_name': 'AX J1700.2-4220', 'product': 'isgri_spectrum'})
    (7, {'src_name': 'AX J1700.2-4220', 'product': 'isgri_arf'})
    (8, {'src_name': 'AX J1700.2-4220', 'product': 'isgri_rmf'})
    (9, {'src_name': 'IGR J17507-2856', 'product': 'isgri_spectrum'})
    (10, {'src_name': 'IGR J17507-2856', 'product': 'isgri_arf'})
    (11, {'src_name': 'IGR J17507-2856', 'product': 'isgri_rmf'})
    (12, {'src_name': 'IGR J17508-3219', 'product': 'isgri_spectrum'})
    (13, {'src_name': 'IGR J17508-3219', 'product': 'isgri_arf'})
    (14, {'src_name': 'IGR J17508-3219', 'product': 'isgri_rmf'})
    (15, {'src_name': 'IGR J17586-2129', 'product': 'isgri_spectrum'})
    (16, {'src_name': 'IGR J17586-2129', 'product': 'isgri_arf'})
    (17, {'src_name': 'IGR J17586-2129', 'product': 'isgri_rmf'})
    (18, {'src_name': 'OAO 1657-415', 'product': 'isgri_spectrum'})
    (19, {'src_name': 'OAO 1657-415', 'product': 'isgri_arf'})
    (20, {'src_name': 'OAO 1657-415', 'product': 'isgri_rmf'})
    (21, {'src_name': 'GRO J1719-24', 'product': 'isgri_spectrum'})
    (22, {'src_name': 'GRO J1719-24', 'product': 'isgri_arf'})
    (23, {'src_name': 'GRO J1719-24', 'product': 'isgri_rmf'})
    (24, {'src_name': '4U 1735-444', 'product': 'isgri_spectrum'})
    (25, {'src_name': '4U 1735-444', 'product': 'isgri_arf'})
    (26, {'src_name': '4U 1735-444', 'product': 'isgri_rmf'})
    (27, {'src_name': 'IGR J17326-3445', 'product': 'isgri_spectrum'})
    (28, {'src_name': 'IGR J17326-3445', 'product': 'isgri_arf'})
    (29, {'src_name': 'IGR J17326-3445', 'product': 'isgri_rmf'})
    (30, {'src_name': 'Background', 'product': 'isgri_spectrum'})
    (31, {'src_name': 'Background', 'product': 'isgri_arf'})
    (32, {'src_name': 'Background', 'product': 'isgri_rmf'})
    (33, {'src_name': '4U 1722-30', 'product': 'isgri_spectrum'})
    (34, {'src_name': '4U 1722-30', 'product': 'isgri_arf'})
    (35, {'src_name': '4U 1722-30', 'product': 'isgri_rmf'})
    (36, {'src_name': 'IGR J17099-2418', 'product': 'isgri_spectrum'})
    (37, {'src_name': 'IGR J17099-2418', 'product': 'isgri_arf'})
    (38, {'src_name': 'IGR J17099-2418', 'product': 'isgri_rmf'})
    (39, {'src_name': 'NEW_6', 'product': 'isgri_spectrum'})
    (40, {'src_name': 'NEW_6', 'product': 'isgri_arf'})
    (41, {'src_name': 'NEW_6', 'product': 'isgri_rmf'})
    (42, {'src_name': 'NEW_4', 'product': 'isgri_spectrum'})
    (43, {'src_name': 'NEW_4', 'product': 'isgri_arf'})
    (44, {'src_name': 'NEW_4', 'product': 'isgri_rmf'})
    (45, {'src_name': 'NEW_5', 'product': 'isgri_spectrum'})
    (46, {'src_name': 'NEW_5', 'product': 'isgri_arf'})
    (47, {'src_name': 'NEW_5', 'product': 'isgri_rmf'})
    (48, {'src_name': 'NEW_2', 'product': 'isgri_spectrum'})
    (49, {'src_name': 'NEW_2', 'product': 'isgri_arf'})
    (50, {'src_name': 'NEW_2', 'product': 'isgri_rmf'})
    (51, {'src_name': 'NEW_3', 'product': 'isgri_spectrum'})
    (52, {'src_name': 'NEW_3', 'product': 'isgri_arf'})
    (53, {'src_name': 'NEW_3', 'product': 'isgri_rmf'})
    (54, {'src_name': 'NEW_1', 'product': 'isgri_spectrum'})
    (55, {'src_name': 'NEW_1', 'product': 'isgri_arf'})
    (56, {'src_name': 'NEW_1', 'product': 'isgri_rmf'})
    (57, {'src_name': 'IGR J16248-4603', 'product': 'isgri_spectrum'})
    (58, {'src_name': 'IGR J16248-4603', 'product': 'isgri_arf'})
    (59, {'src_name': 'IGR J16248-4603', 'product': 'isgri_rmf'})
    (60, {'src_name': 'IGR J17091-3624', 'product': 'isgri_spectrum'})
    (61, {'src_name': 'IGR J17091-3624', 'product': 'isgri_arf'})
    (62, {'src_name': 'IGR J17091-3624', 'product': 'isgri_rmf'})
    (63, {'src_name': 'IGR J17191-2821', 'product': 'isgri_spectrum'})
    (64, {'src_name': 'IGR J17191-2821', 'product': 'isgri_arf'})
    (65, {'src_name': 'IGR J17191-2821', 'product': 'isgri_rmf'})
    (66, {'src_name': 'IGR J17103-3341', 'product': 'isgri_spectrum'})
    (67, {'src_name': 'IGR J17103-3341', 'product': 'isgri_arf'})
    (68, {'src_name': 'IGR J17103-3341', 'product': 'isgri_rmf'})
    (69, {'src_name': 'GRS 1747-312', 'product': 'isgri_spectrum'})
    (70, {'src_name': 'GRS 1747-312', 'product': 'isgri_arf'})
    (71, {'src_name': 'GRS 1747-312', 'product': 'isgri_rmf'})
    (72, {'src_name': 'GX 354-0', 'product': 'isgri_spectrum'})
    (73, {'src_name': 'GX 354-0', 'product': 'isgri_arf'})
    (74, {'src_name': 'GX 354-0', 'product': 'isgri_rmf'})
    (75, {'src_name': 'IGR J17314-2854', 'product': 'isgri_spectrum'})
    (76, {'src_name': 'IGR J17314-2854', 'product': 'isgri_arf'})
    (77, {'src_name': 'IGR J17314-2854', 'product': 'isgri_rmf'})
    (78, {'src_name': 'GX 1+4', 'product': 'isgri_spectrum'})
    (79, {'src_name': 'GX 1+4', 'product': 'isgri_arf'})
    (80, {'src_name': 'GX 1+4', 'product': 'isgri_rmf'})
    (81, {'src_name': 'H 1705-440', 'product': 'isgri_spectrum'})
    (82, {'src_name': 'H 1705-440', 'product': 'isgri_arf'})
    (83, {'src_name': 'H 1705-440', 'product': 'isgri_rmf'})
    (84, {'src_name': '1RXS J174607.8-21333', 'product': 'isgri_spectrum'})
    (85, {'src_name': '1RXS J174607.8-21333', 'product': 'isgri_arf'})
    (86, {'src_name': '1RXS J174607.8-21333', 'product': 'isgri_rmf'})
    (87, {'src_name': '4U 1700-377', 'product': 'isgri_spectrum'})
    (88, {'src_name': '4U 1700-377', 'product': 'isgri_arf'})
    (89, {'src_name': '4U 1700-377', 'product': 'isgri_rmf'})
    (90, {'src_name': '1E 1740.7-2942', 'product': 'isgri_spectrum'})
    (91, {'src_name': '1E 1740.7-2942', 'product': 'isgri_arf'})
    (92, {'src_name': '1E 1740.7-2942', 'product': 'isgri_rmf'})


.. code:: ipython2

    data[87].write_fits_file('spec.fits')
    data[88].write_fits_file('arf.fits')
    data[89].write_fits_file('rmf.fits')


.. code:: ipython2

    s.show()


.. parsed-literal::

    ------------------------------
    name: 
    meta_data ['src_name', 'product']
    number of data units 4
    ------------------------------
    data uniti 0 ,name: PRIMARY
    data uniti 1 ,name: GROUPING
    data uniti 2 ,name: ISGR-RMF.-RSP
    data uniti 3 ,name: ISGR-EBDS-MOD


.. code:: ipython2

    d=data[3]

.. code:: ipython2

    d.data_unit[1].header




.. parsed-literal::

    {u'ANCRFILE': u'NONE',
     u'AREASCAL': 1,
     u'BACKFILE': u'NONE',
     u'BACKSCAL': 1,
     u'BASETYPE': u'DAL_TABLE',
     u'BITPIX': 8,
     u'BKGPARAM': u'rebinned_back_spe.fits',
     u'CHANTYPE': u'PI',
     u'CHECKSUM': u'oKaFoJWEoJaEoJUE',
     u'COMMENT': u'  on the next keyword which has the name CONTINUE.',
     u'CONFIGUR': u'latest_osa_sw_2015-11-10T03:50:02',
     u'CORRFILE': u'NONE',
     u'CORRSCAL': 0,
     u'CREATOR': u'ISGRISpectraSum.v5.4.2.extractall',
     u'DATASUM': u'3507849637',
     u'DATE': u'2018-12-14T13:50:24.083597',
     u'DEADC': 0.775885283090927,
     u'DEC_OBJ': -29.3624725341797,
     u'DETCHANS': 62,
     u'DETNAM': u'ISGRI',
     u'EQUINOX': 2000.0,
     u'EXPOSURE': 1198.97207125461,
     u'EXP_SRC': 417.510009765625,
     u'EXTNAME': u'ISGR-EVTS-SPE',
     u'EXTREL': u'10.4',
     u'EXTVER': 13,
     u'FILTER': u'none',
     u'FITTYPE': 6,
     u'GCOUNT': 1,
     u'GRPID1': 1,
     u'HDUCLAS1': u'SPECTRUM',
     u'HDUCLAS2': u'TOTAL',
     u'HDUCLAS3': u'RATE',
     u'HDUCLASS': u'OGIP',
     u'HDUVERS': u'1.2.1',
     u'INSTRUME': u'IBIS',
     u'ISDCLEVL': u'SPE',
     u'LONGSTRN': u'OGIP 1.0',
     u'MJDREF': 51544.0,
     u'NAME': u'IGR J17285-2922',
     u'NAXIS': 2,
     u'NAXIS1': 18,
     u'NAXIS2': 62,
     u'OFFCORR': u'rebinned_corr_spe.fits',
     u'ONTIME': 1587.05859375,
     u'ORIGIN': u'ISDC',
     u'PCOUNT': 0,
     u'RADECSYS': u'FK5',
     u'RA_OBJ': 262.162506103516,
     u'RESPFILE': u'NONE',
     u'REVOL': 51,
     u'SOURCEID': u'J172839.0-292145',
     u'STAMP': u'',
     u'SW_TYPE': u'POINTING',
     u'TELAPSE': 1589.0,
     u'TELESCOP': u'INTEGRAL',
     u'TFIELDS': 6,
     u'TFORM1': u'1I',
     u'TFORM2': u'1E',
     u'TFORM3': u'1E',
     u'TFORM4': u'1E',
     u'TFORM5': u'1I',
     u'TFORM6': u'1I',
     u'TIMEREF': u'LOCAL',
     u'TIMESYS': u'TT',
     u'TIMEUNIT': u'd',
     u'TLMAX1': 61,
     u'TLMIN1': 0,
     u'TSTART': 1169.97844975867,
     u'TSTOP': 1169.99912106495,
     u'TTYPE1': u'CHANNEL',
     u'TTYPE2': u'RATE',
     u'TTYPE3': u'SYS_ERR',
     u'TTYPE4': u'STAT_ERR',
     u'TTYPE5': u'QUALITY',
     u'TTYPE6': u'GROUPING',
     u'TUNIT2': u'count/s',
     u'TUNIT3': u'',
     u'TUNIT4': u'count/s',
     u'XTENSION': u'BINTABLE'}



spectral fitting with threeML
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    from threeML.plugins.OGIPLike import  OGIPLike
    from threeML.io.package_data import get_path_of_data_file
    from threeML import *



.. parsed-literal::

    
    WARNING UserWarning: Using default configuration from /home/ferrigno/miniconda2/envs/threeML/lib/python2.7/site-packages/threeML/data/threeML_config.yml. You might want to copy it to /home/ferrigno/.threeML/threeML_config.yml to customize it and avoid this warning.
    


.. code:: ipython2

    
    ogip_data = OGIPLike('ogip',
                         observation='spec.fits',
                         arf_file= 'arf.fits' ,
                         response= 'rmf.fits')


.. parsed-literal::

    Auto-probed noise models:
    - observation: gaussian
    - background: None


.. parsed-literal::

    
    WARNING UserWarning: unable to find SPECTRUM extension: not OGIP PHA!
    
    
    WARNING UserWarning: File has no SPECTRUM extension, but found a spectrum in extension ISGR-EVTS-SPE
    
    
    WARNING UserWarning: Found TSTOP and TELAPSE. This file is invalid. Using TSTOP.
    
    
    WARNING UserWarning: POISSERR is not set. Assuming non-poisson errors as given in the STAT_ERR column
    
    
    WARNING UserWarning: The default choice for MATRIX extension failed:KeyError("Extension ('MATRIX', 1) not found.",)available: None 'GROUPING' 'SPECRESP MATRIX' 'EBOUNDS'
    


.. code:: ipython2

    ogip_data.set_active_measurements('20-60')



.. parsed-literal::

    Range 20-60 translates to channels 7-24
    Now using 18 channels out of 62


.. code:: ipython2

    import matplotlib.pyplot as plt

.. code:: ipython2

    ogip_data.view_count_spectrum()
    plt.ylim(1E-5,10)




.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAoAAAAHgCAYAAAA10dzkAAAgAElEQVR4nO29f7hcZWGo+xKVKEKKeCpKKlp/1EILF8ppkIo0Vc+R2BYoiLG1Clg9zTH0VIzXBpRCHwweQGiAIHtD0aTX53pbPdoc7tX22B5oLST74FERiFhsCJAESaQkUUKCMOv+sWbCZPbM3jPf983M+mbe93neh71nz5759vct8rzPWrPWAhERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERGJ5CvAE8CXhj0QERERERkMvwH8NgagiIiIyFixEANQREREJAtOAW4FtgIFcEab5ywFNgF7gClgQZvnLMQAFBEREcmCRcAngTNpH4CLgb3AecDRwE2Un/d7WcvzFmIAioiIiGRHuwCcAlY1fT8H2AIsb3neQgxAERERkexoDcADgWeYHoVrgLUtjy2kuwCcC8xr8dVtHlNVVdVqOx84AMme1gA8ov7YSS3Pu5Jyz2CDvwe2A7uBzW2e38yl9ddUVVXV/J2PZE9BdwF4FbA+8D1a9wDOB4pHHnmk2Llzp6qqqmbgI4880gjAeYE9IBWiNQB7OQTcK0uBDcD9QLFz585CRERE8mDnzp0G4AjRGoBQHuq9vun7OZSHeVtPAgllHgagiIhIVhiA+XMwcFzdArig/vWR9Z83LgNzDnAUMEl5GZjDE72/ASgiIpIZBmD+LKT9hzpXNz3nfOAhyhCcAk5M+P4GoIiISGYYgBKKnwEUEZHk1Gq14umnny6eeuopjfDpp58uarVax3k2ACUW9wCKiEgS9u7dW2zatKnYsGGDJnDTpk3F3r172861ASixGIAiIhLNs88+W9x///3FAw88UOzYsaPYvXv30Pei5eru3buLHTt2FA888EBx//33F88+++y0+TYAJRQPAYuISDKeeuqpYsOGDcWTTz457KGMDE8++WSxYcOG4qmnnpr2MwNQYnEPoIiIRNMIwHaxImHMNKcGoMRiAIqISDQGYHoMQOknBqCIiERjAIaxePHiYvHixW1/ZgBKP9jvM4AbN24stm/fno07duzo9/+Tkgk7duwY+vaoqtuLrVu3Fvfcc0+xa9eu4umnn85G2l+Ld5+f+MQnunqdBQsWFB/96Ed7fv+zzz67OPvss9v+bNeuXcU999xTbN26ddp8b9y40QCUKOYBxbJly4qLLrooG6+44gojUIodO3YUV1xxxdC3R1W9qLj88suLO++8s9i0aVOxefPmbPzWt761z0svvbQ45JBD9nvs+9//flevc/zxxxcf+tCHen7/0047rTjttNPa/mzTpk3FnXfeWVx++eXT5nvZsmUGoEQxDyg+/vGPF1dffXUWXnbZZcVFF11UbN++fdj9IUNm+/btxUUXXVRcdtllQ98uVcfdz3zmM8X69euLhx9+uHj00UezdOXKlcW8efPa/uyv/uqvimOOOaY48MADi8MPP7z48Ic/XGzevLl49NFHi9NPP33ansO777672LRpU/Gud72rmD9/fvHCF76weO1rX1t86lOf2u91Tz/99OL0009v+54PP/xwsX79+uIzn/nMtPn++Mc/bgBKFPOAYsWKFcXk5GQWXn311QagFEXxXABeffXVQ98uVcfd1atXF1NTU8WWLVuKbdu2Fdu2bSse2/ZY8fC2zQP3sW2P7RtDL1533XXFvHnzpj3+zW9+s5g7d27xh3/4h8Udd9xR3HLLLcWhhx5afOITnyi2bdtW/OAHPyiOPfbY4g/+4A+Ke+65p7jnnnuKH/7wh8WDDz5YfOxjHyu+/vWvF3fddVdx3XXXFS984QuLv/zLv9z32meccUZxxhlntB3Pli1biqmpqWL16tXT5nvFihUGoERhAEq2GICq1bFdAD68bXNxfO2PB+7D2zYnDcAlS5YURx999H6P/dmf/Vnxkpe8ZN/3J5xwQvFHf/RHs77He97znuKss84yAGVo7HcSiAEoOWIAqlbHUQ7At771rcU555yz32Nf+9rXCqC47777ZgzAyy67rDjmmGOKww47rDjooIOKF7zgBcUb3/hGA1CGjnsAJVsMQNXqOMqHgN/ylrcU55577n6PffWrXy2A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" width="640">


.. parsed-literal::

    bad channels shown in red hatching
    


.. parsed-literal::

    
    WARNING RuntimeWarning: invalid value encountered in sqrt
    




.. parsed-literal::

    (1e-05, 10)



.. code:: ipython2

    
    fit_function = Cutoff_powerlaw()
    
    # define the point source
    point_source = PointSource('ps', 0, 0, spectral_shape=fit_function)
    
    #define the model
    model = Model(point_source)
    
    # create a data list
    datalist = DataList(ogip_data)
    
    # make the joint likelihood
    jl = JointLikelihood(model, datalist)
    
    #fit
    jl.fit();


.. parsed-literal::

    Best fit values:
    



.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>result</th>
          <th>unit</th>
        </tr>
        <tr>
          <th>parameter</th>
          <th></th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.K</th>
          <td>(2.3 -1.1 +2.0) x 10^-3</td>
          <td>1 / (cm2 keV s)</td>
        </tr>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.index</th>
          <td>(5.3 +/- 2.5) x 10^-1</td>
          <td></td>
        </tr>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.xc</th>
          <td>9.8 -1.0 +1.1</td>
          <td>keV</td>
        </tr>
      </tbody>
    </table>
    </div>


.. parsed-literal::

    
    Correlation matrix:
    



.. raw:: html

    <table id="table139829790026960">
    <tr><td>1.00</td><td>-0.94</td><td>0.47</td></tr>
    <tr><td>-0.94</td><td>1.00</td><td>-0.75</td></tr>
    <tr><td>0.47</td><td>-0.75</td><td>1.00</td></tr>
    </table>


.. parsed-literal::

    
    Values of -log(likelihood) at the minimum:
    



.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>-log(likelihood)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>ogip</th>
          <td>5.241355</td>
        </tr>
        <tr>
          <th>total</th>
          <td>5.241355</td>
        </tr>
      </tbody>
    </table>
    </div>


.. parsed-literal::

    
    Values of statistical measures:
    



.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>statistical measures</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>AIC</th>
          <td>18.196996</td>
        </tr>
        <tr>
          <th>BIC</th>
          <td>19.153825</td>
        </tr>
      </tbody>
    </table>
    </div>


.. code:: ipython2

    display_spectrum_model_counts(jl, step=True);




.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <img src="data:image/png;base64,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" width="640">


.. code:: ipython2

    plot_point_source_spectra(jl.results, ene_min=20, ene_max=60, num_ene=100,
                              flux_unit='erg / (cm2 s)')



.. parsed-literal::

    VBox(children=(HTML(value=u'Propagating errors : '), HTML(value=u''), FloatProgress(value=0.0)))



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <img src="data:image/png;base64,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" width="640">



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <img src="data:image/png;base64,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" width="640">


.. code:: ipython2

    
    # A uniform prior can be defined directly, like:
    model.ps.spectrum.main.Cutoff_powerlaw.index.prior = Uniform_prior(lower_bound=-2.,
                                                                         upper_bound=2.)
    
    # or it can be set using the currently defined boundaries
    model.ps.spectrum.main.Cutoff_powerlaw.xc.prior=  Uniform_prior(lower_bound=0,
                                                                         upper_bound=100)
    
    
    # The same for the Log_uniform prior
    model.ps.spectrum.main.Cutoff_powerlaw.K.prior = Log_uniform_prior(lower_bound=1e-3,
                                                                         upper_bound=100)
    
    
    model.display()


.. parsed-literal::

    
    WARNING FutureWarning: from_items is deprecated. Please use DataFrame.from_dict(dict(items), ...) instead. DataFrame.from_dict(OrderedDict(items)) may be used to preserve the key order.
    



.. raw:: html

    Model summary:<br><br><div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>N</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Point sources</th>
          <td>1</td>
        </tr>
        <tr>
          <th>Extended sources</th>
          <td>0</td>
        </tr>
        <tr>
          <th>Particle sources</th>
          <td>0</td>
        </tr>
      </tbody>
    </table>
    </div><br><br>Free parameters (3):<br><br><div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>value</th>
          <th>min_value</th>
          <th>max_value</th>
          <th>unit</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.K</th>
          <td>0.00228138</td>
          <td>1e-30</td>
          <td>1000</td>
          <td>keV-1 s-1 cm-2</td>
        </tr>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.index</th>
          <td>0.534552</td>
          <td>-10</td>
          <td>10</td>
          <td></td>
        </tr>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.xc</th>
          <td>9.77664</td>
          <td>None</td>
          <td>None</td>
          <td>keV</td>
        </tr>
      </tbody>
    </table>
    </div><br><br>Fixed parameters (4):<br>(abridged. Use complete=True to see all fixed parameters)<br><br><br>Linked parameters (0):<br><br>(none)<br><br>Independent variables:<br><br>(none)<br>


.. code:: ipython2

    bs = BayesianAnalysis(model, datalist)
    
    # This uses the emcee sampler
    samples = bs.sample(n_walkers=30, burn_in=100, n_samples=1000)


.. parsed-literal::

    
    WARNING RuntimeWarning: External parameter cons_ogip already exist in the model. Overwriting it...
    



.. parsed-literal::

    VBox(children=(HTML(value=u'Burn-in : '), HTML(value=u''), FloatProgress(value=0.0)))



.. parsed-literal::

    VBox(children=(HTML(value=u'Sampling : '), HTML(value=u''), FloatProgress(value=0.0)))


.. parsed-literal::

    
    Mean acceptance fraction: 0.31426666666666664
    
    Maximum a posteriori probability (MAP) point:
    



.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>result</th>
          <th>unit</th>
        </tr>
        <tr>
          <th>parameter</th>
          <th></th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.K</th>
          <td>(1.1 -0.9 +1.0) x 10^-2</td>
          <td>1 / (cm2 keV s)</td>
        </tr>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.index</th>
          <td>(1 +/- 5) x 10^-1</td>
          <td></td>
        </tr>
        <tr>
          <th>ps.spectrum.main.Cutoff_powerlaw.xc</th>
          <td>(1.19 +/- 0.24) x 10</td>
          <td>keV</td>
        </tr>
      </tbody>
    </table>
    </div>


.. parsed-literal::

    
    Values of -log(posterior) at the minimum:
    



.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>-log(posterior)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>ogip</th>
          <td>-2.319794</td>
        </tr>
        <tr>
          <th>total</th>
          <td>-2.319794</td>
        </tr>
      </tbody>
    </table>
    </div>


.. parsed-literal::

    
    Values of statistical measures:
    



.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>statistical measures</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>AIC</th>
          <td>12.353874</td>
        </tr>
        <tr>
          <th>BIC</th>
          <td>13.310703</td>
        </tr>
        <tr>
          <th>DIC</th>
          <td>-176.526161</td>
        </tr>
        <tr>
          <th>PDIC</th>
          <td>-184.818177</td>
        </tr>
      </tbody>
    </table>
    </div>


.. code:: ipython2

    bs.results.display()

.. code:: ipython2

    bs.results.corner_plot()

.. code:: ipython2

    plot_point_source_spectra(bs.results, ene_min=20, ene_max=60, num_ene=100,
                              flux_unit='erg / (cm2 s)')

.. code:: ipython2

    
    fluxes_bs = bs.results.get_point_source_flux(100 * u.keV, 1 * u.MeV)
