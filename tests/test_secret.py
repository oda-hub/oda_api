import os
import pytest
from oda_api.secret import get_secret

@pytest.fixture
def secrets_path(tmp_path):
    os.environ['ODA_SECRET_STORAGE'] = str(tmp_path)
    yield tmp_path
    del os.environ['ODA_SECRET_STORAGE']

def test_renku_secret(secrets_path):
    secret = 'secret'
    secret_name = 's'
    with open(secrets_path / secret_name, 'w') as f:
        f.write(secret)
    assert get_secret(secret_name) == secret
