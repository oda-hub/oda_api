from typing import Optional
import os

def get_secret(secret_name: str) -> str:
    # Get secret by name
    # For now only default renku file secret storage is supported whuch stores secrets as plain text

    secrets_dir = os.getenv('ODA_SECRET_STORAGE', '/secrets')  # check for default secret location in renku platform
    secrets_file = os.path.join(secrets_dir, secret_name)
    if os.path.isfile(secrets_file):
        with open(secrets_file, 'r') as f:
            return f.read()
