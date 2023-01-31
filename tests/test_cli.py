from typing import ChainMap
from click.testing import CliRunner
import pytest
import os

from oda_api import cli


@pytest.mark.parametrize('token_placement', ['no', 'env', 'homedotfile', 'cwddotfile'])
def test_token_inspect(token_placement, default_token, monkeypatch, caplog, tmpdir):
    # reset any existing token locations    
    os.makedirs(tmpdir, exist_ok=True)    
    monkeypatch.setenv('HOME', tmpdir)

    oda_token_home_fn = os.path.join(tmpdir, ".oda-token")
    if os.path.exists(oda_token_home_fn):
        os.remove(oda_token_home_fn)

    oda_token_cwd_fn = ".oda-token"
    if os.path.exists(oda_token_cwd_fn):
        os.remove(oda_token_cwd_fn)
    
    monkeypatch.setenv('ODA_TOKEN', '')

    if token_placement == 'env':
        monkeypatch.setenv('ODA_TOKEN', default_token)    
        
    elif token_placement == 'cwddotfile':
        with open(oda_token_cwd_fn, "w") as f:
            f.write(default_token)

    elif token_placement == 'homedotfile':
        with open(oda_token_home_fn, "w") as f:
            f.write(default_token)

    runner = CliRunner()
    result = runner.invoke(cli.tokencli, ['inspect'], obj={})

    if token_placement == 'no':
        assert result.exit_code == 1
        assert 'failed to discover token with any known method' in caplog.text
    else:
        assert result.exit_code == 0
        assert '"sub": "mtm@mtmco.net"' in caplog.text
        assert '"mssub": true' in caplog.text    

def test_token_modify(default_token, secret_key, monkeypatch, caplog):
    monkeypatch.setenv('ODA_TOKEN', default_token)

    runner = CliRunner()
    result = runner.invoke(cli.tokencli, ['inspect'], obj={})
    assert result.exit_code == 0

    assert '"mssub": true' in caplog.text    
    assert '"msdone": false' not in caplog.text    
    
    runner = CliRunner()
    result = runner.invoke(cli.tokencli, ['-s', secret_key, 'modify', "--disable-email", "--new-validity-hours", "100"], obj={})
    assert result.exit_code == 0
        
    assert '"sub": "mtm@mtmco.net"' in caplog.text
    assert 'your current token payload:' in caplog.text    
    assert 'your new token payload:' in caplog.text    
    assert '"msdone": false' in caplog.text    
    assert '"mssub": false' in caplog.text    
    
def test_get(dispatcher_live_fixture, caplog):
    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, 'get'], obj={})
    assert result.exit_code == 0

    assert "found instruments: ['empty', 'empty-async', 'empty-semi-async']" in caplog.text or \
           "found instruments: ['empty', 'empty-async', 'empty-semi-async', 'isgri', 'jemx', 'osa_fake']" in caplog.text

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, 'get', '-i', 'empty'], obj={})
    assert result.exit_code == 0
    assert "'prod_dict': {'dummy': 'empty_parameters_dummy_query', 'echo': 'echo_parameters_dummy_query', 'failing': '" in caplog.text

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, '--no-wait', 'get', '-i', 'empty', '-p', 'dummy', '-a', 'product_type=Dummy'], obj={})
    assert result.exit_code == 0
