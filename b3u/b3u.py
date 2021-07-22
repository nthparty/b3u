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

    >>> credentials('s3://abc:xyz@bucket/object.data')
    {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}
    >>> cs = credentials('s3://abc:xyz:123@bucket/object.data')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    aws_session_token 123
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

    >>> configuration('s3://abc:xyz@bucket/object.data')
    {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}
    >>> cs = configuration('s3://abc:xyz:123@bucket/object.data')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    aws_session_token 123
    >>> cs = configuration('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    region_name us-east-1
    >>> cs = configuration('s3://bucket/object.data?region_name=us-east-1')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    region_name us-east-1
    """
    params = credentials(uri)
    result = parse_qs(urlparse(uri).query)

    for (key, values) in result.items():
        if len(values) == 1:
            params[key] = values[0]

    return params

def for_client(uri: str) -> dict:
    """
    Extract all parameters for a client constructor.

    >>> ps = for_client('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
    >>> for (k, v) in sorted(ps.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    region_name us-east-1
    service_name s3
    """
    result = urlparse(uri)
    params = configuration(uri)
    params['service_name'] = result.scheme
    return params

def for_get(uri: str) -> dict:
    """
    Extract resource names from a URI for supported AWS services.

    >>> for_get('s3://abc:xyz@bucket/object.data')
    {'Bucket': 'bucket', 'Key': 'object.data'}
    >>> for_get('ssm://ABC:XYZ@/path/to/parameter?region_name=us-east-1')
    {'Name': '/path/to/parameter'}
    """
    params = {}
    result = urlparse(uri)

    if result.scheme == 's3':
        if result.hostname is not None and result.hostname != '':
            params['Bucket'] = result.hostname
        if result.path is not None and result.path != '':
            params['Key'] = result.path.lstrip('/')
    elif result.scheme == 'ssm':
        if result.path is not None and result.path != '':
            params['Name'] = result.path

    return params

# Succinct synonyms.
cred = credentials
conf = configuration

if __name__ == "__main__":
    doctest.testmod() # pragma: no cover
