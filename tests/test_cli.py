from typing import ChainMap
from click.testing import CliRunner
import pytest
import os

from oda_api import cli


@pytest.mark.parametrize('token_placement', ['env', 'homedotfile', 'cwddotfile'])
def test_token_inspect(token_placement, default_token, monkeypatch, caplog):
    if token_placement == 'env':
        monkeypatch.setenv('ODA_TOKEN', default_token)
    elif token_placement == 'cwddotfile':
        with open(".oda-token", "w") as f:
            f.write(default_token)
    elif token_placement == 'homedotfile':
        fakehome = "fake-home"
        os.makedirs(fakehome, exist_ok=True)
        monkeypatch.setenv('HOME', fakehome)
        with open(os.path.join(fakehome, ".oda-token"), "w") as f:
            f.write(default_token)

    runner = CliRunner()
    result = runner.invoke(cli.tokencli, ['inspect'], obj={})
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
    assert "found instruments: ['empty', 'empty-async', 'empty-semi-async']" in caplog.text

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, 'get', '-i', 'empty'], obj={})
    assert result.exit_code == 0
    assert "'prod_dict': {'dummy': 'empty_parameters_dummy_query', 'numerical': '" in caplog.text

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, '--no-wait', 'get', '-i', 'empty', '-p', 'dummy', '-a', 'product_type=Dummy'], obj={})
    assert result.exit_code == 0
