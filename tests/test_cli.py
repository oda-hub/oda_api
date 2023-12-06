import re
from typing import ChainMap
from click.testing import CliRunner
import pytest
import os
import jwt

from oda_api import cli
from tests.test_basic import default_token_payload, secret_key


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
    result = runner.invoke(cli.tokencli, ['-s', secret_key, 'modify', "--disable-email", "--new-validity-hours", "100", "--disable-matrix", "--matrix-room-id", "test_room_id:matrix.org"], obj={})
    assert result.exit_code == 0
        
    assert '"sub": "mtm@mtmco.net"' in caplog.text
    assert 'your current token payload:' in caplog.text    
    assert 'your new token payload:' in caplog.text    
    assert '"msdone": false' in caplog.text    
    assert '"mssub": false' in caplog.text
    assert '"mxdone": false' in caplog.text
    assert '"mxsub": false' in caplog.text
    assert '"mxroomid": "test_room_id:matrix.org"' in caplog.text

def test_get(dispatcher_live_fixture, caplog, monkeypatch, tmpdir):
    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, 'get'], obj={})
    assert result.exit_code == 0

    assert re.search(r"found instruments: \[.*\]", caplog.text)

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, 'get', '-i', 'empty'], obj={})
    assert result.exit_code == 0
    assert "'prod_dict': {'dummy': 'empty_parameters_dummy_query', 'echo': 'echo_parameters_dummy_query', 'failing': '" in caplog.text

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, '--no-wait', 'get', '-i', 'empty', '-p', 'dummy', '-a', 'product_type=Dummy'], obj={})
    assert result.exit_code == 0

    runner = CliRunner()
    result = runner.invoke(cli.cli,
                           ['-u', dispatcher_live_fixture, '--no-wait', 'get'], obj={})
    assert result.exit_code == 0

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, '--no-wait', 'get', '-i', 'empty'], obj={})
    assert result.exit_code == 0

    # using the discovering token arg
    token_payload = default_token_payload.copy()
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    runner = CliRunner()
    token_write_method = 'oda_env_var'
    monkeypatch.setenv('ODA_TOKEN', encoded_token)
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, '--no-wait', 'get', '-i', 'empty', '-T', token_write_method], obj={})
    assert result.exit_code == 0
    os.environ.pop('ODA_TOKEN', None)

    runner = CliRunner()
    token_write_method = 'file_home'
    os.makedirs(tmpdir, exist_ok=True)
    monkeypatch.setenv('HOME', tmpdir)
    oda_token_home_fn = os.path.join(tmpdir, ".oda-token")
    token_payload['exp'] = token_payload['exp'] + 15000
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    with open(oda_token_home_fn, "w") as f:
        f.write(encoded_token)
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, '--no-wait', 'get', '-i', 'empty', '-T', token_write_method], obj={})
    assert result.exit_code == 0
    os.remove(oda_token_home_fn)

    runner = CliRunner()
    token_write_method = 'file_cur_dir'
    token_payload['exp'] = token_payload['exp'] + 15000
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    with open(".oda-token", "w") as f:
        f.write(encoded_token)
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, '--no-wait', 'get', '-i', 'empty', '-T', token_write_method], obj={})
    assert result.exit_code == 0
    os.remove(os.path.join(os.getcwd(), ".oda-token"))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-u', dispatcher_live_fixture, '--no-wait', 'get', '-i', 'empty', '-T', token_write_method], obj={})
    assert result.exit_code == 0

    assert "A token could not be found with the desired method, if present, the one automatically discovered will be used" in caplog.text
