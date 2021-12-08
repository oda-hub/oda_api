import pathlib

import pytest

@pytest.mark.live
def test_plot_tools_notebook(request):
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
