"""Boto3 data extraction from URIs.

Boto3 URI utility library that supports extraction of
Boto3 configuration data from AWS resource URIs.
"""

from __future__ import annotations
import doctest
from urllib.parse import urlparse, parse_qs

def credentials(uri: str) -> dict:
    """
    Extract configuration data (only credentials from a URI.
    """
    params = {}
    result = urlparse(uri)

    if result.username is not None and result.username != '':
        params['aws_access_key_id'] = result.username

    if result.password is not None and result.password != '':
        if not ':' in result.password:
            params['aws_secret_access_key'] = result.password
        else:
            (secret, token) = result.password.split(':')
            params['aws_secret_access_key'] = secret
            params['aws_session_token'] = token

    return params

def configuration(uri: str) -> dict:
    """
    Extract configuration data (both credentials and
    non-credentials) from a URI.
    """
    params = credentials(uri)
    result = parse_qs(urlparse(uri).query)

    for (key, values) in result.items():
        if len(values) == 1:
            params[key] = values[0]

    return params

# Succinct synonyms.
conf = configuration
cred = credentials

if __name__ == "__main__":
    doctest.testmod()
