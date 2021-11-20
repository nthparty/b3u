"""
Boto3 URI utility library that supports extraction of
Boto3 configuration data from AWS resource URIs.
"""
from __future__ import annotations
import doctest
from urllib.parse import urlparse, parse_qs, quote, unquote, ParseResult

def credentials(uri: str) -> dict:
    """
    Extract configuration data (only credentials) from a URI string.

    >>> credentials('s3://abc:xyz@bucket/object.data')
    {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}

    The format ``abc:xyz:123`` can be used to specify a session
    token (which is the third component, ``123``, in this example)
    as part of a URI.

    >>> cs = credentials('s3://abc:xyz:123@bucket/object.data')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    aws_session_token 123

    Credential information can contain the ``/`` character, accommodating
    more complex scenarios.

    >>> cs = credentials('s3://abc:/abcdef/ghijklmnopqrstuvwxyz/1234567890/@bucket/object.data')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key /abcdef/ghijklmnopqrstuvwxyz/1234567890/

    >>> cs = credentials('s3://abc:/abcdef/ghijklmnopqrstuvwxyz/1234567890/:123@bucket/object.data')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key /abcdef/ghijklmnopqrstuvwxyz/1234567890/
    aws_session_token 123
    """
    params = {}
    result = _make_url_safe(uri)

    if result.username is not None and result.username != '':
        params['aws_access_key_id'] = result.username

    if result.password is not None and result.password != '':
        if not ':' in result.password:
            params['aws_secret_access_key'] = unquote(result.password)
        else:
            (secret, token) = result.password.split(':')
            params['aws_secret_access_key'] = unquote(secret)
            params['aws_session_token'] = token

    return params

def configuration(uri: str, safe: bool = True) -> dict:
    """
    Extract configuration data (both credentials and non-credentials)
    from a URI string.

    >>> configuration('s3://abc:xyz@bucket/object.data')
    {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}

    The format ``abc:xyz:123`` can be used to specify a session
    token (which is ``123`` in this case).

    >>> cs = configuration('s3://abc:xyz:123@bucket/object.data')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    aws_session_token 123

    The value for the parameter ``region_name`` can be specified in the
    manner illustrated below.

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

    Other named parameters in the URI are ignored by default, but can be
    included by setting the function parameter ``safe`` to ``False``.

    >>> cs = configuration('s3://bucket/object.data?other_param=other_value')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)

    >>> cs = configuration('s3://bucket/object.data?other_param=other_value', False)
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    other_param other_value

    >>> cs = configuration('s3://bucket/object.data?other_param=other:value', False)
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    other_param other:value
    """
    params = credentials(uri)
    result = parse_qs(_make_url_safe(uri).query)

    for (key, values) in result.items():
        if len(values) == 1:
            if not safe or key in [
                'aws_access_key_id', 'aws_secret_access_key',
                'aws_session_token', 'region_name'
            ]:
                params[key] = values[0]

    return params

def for_client(uri: str, safe: bool = True) -> dict:
    """
    Extract parameters for a client constructor from a URI string.

    >>> ps = for_client('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
    >>> for (k, v) in sorted(ps.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    region_name us-east-1
    service_name s3

    By default, only the parameters ``service_name``, ``region_name``,
    ``api_version``, ``endpoint_url``, ``verify``, ``aws_access_key_id``,
    ``aws_secret_access_key``, ``aws_session_token``, and ``config`` are
    extracted from the URI string.

    >>> ps = for_client('s3://abc:xyz@bucket/object.data?other_param=other_value')
    >>> for (k, v) in sorted(ps.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    service_name s3

    Other named parameters in the URI string are ignored by default, but can
    be included by setting the function parameter ``safe`` to ``False``.

    >>> ps = for_client('s3://abc:xyz@bucket/object.data?other_param=other_value', False)
    >>> for (k, v) in sorted(ps.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    other_param other_value
    service_name s3
    """
    result = _make_url_safe(uri)
    params = configuration(uri, False)
    params['service_name'] = result.scheme

    # Keep only those parameters that correspond to named arguments
    # of the target method.
    if safe:
        params = {
            param: value
            for (param, value) in params.items()
            if param in [
                'service_name', 'region_name', 'api_version', 'endpoint_url',
                'verify', 'aws_access_key_id', 'aws_secret_access_key',
                'aws_session_token', 'config'
            ]
        }

    return params

def for_resource(uri: str, safe: bool = True) -> dict:
    """
    Extract parameters for a resource constructor from a URI string.
    This function is a synonym for the :obj:`for_client` function.

    >>> ps = for_resource('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
    >>> for (k, v) in sorted(ps.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    region_name us-east-1
    service_name s3
    """
    return for_client(uri, safe)

def _make_url_safe(uri: str) -> ParseResult:
    """
    URL encode slashes in ``aws_secret_access_key`` to ensure compatibility
    with ``urlparse``.

    :param uri: AWS resource URI
    :return: URL parsed URI with slahes in ``aws_secret_access_key`` encoded
    """
    parts = uri.split(':')
    if len(parts) >= 3:
        key_and_bucket = parts[2].split('@')
        if len(key_and_bucket[0]) == 40:
            key_and_bucket[0] = quote(key_and_bucket[0], safe='')

        if len(parts) >= 4:
            uri = ':'.join(parts[:2]) + ':' + ''.join(key_and_bucket) + ':' + ':'.join(parts[3:])
        else:
            uri = ':'.join(parts[:2]) + ':' + '@'.join(key_and_bucket)
    return urlparse(uri)

def for_get(uri: str) -> dict:
    """
    Extract resource names from a URI for supported AWS services.
    Currently, only S3 and SSM are supported.

    >>> for_get('s3://abc:xyz@bucket/object.data')
    {'Bucket': 'bucket', 'Key': 'object.data'}
    >>> for_get('ssm://ABC:XYZ@/path/to/parameter?region_name=us-east-1')
    {'Name': '/path/to/parameter'}
    """
    params = {}
    result = _make_url_safe(uri)

    if result.scheme == 's3':
        if result.hostname is not None and result.hostname != '':
            params['Bucket'] = result.hostname
        if result.path is not None and result.path != '':
            params['Key'] = result.path.lstrip('/')
    elif result.scheme == 'ssm':
        if result.path is not None and result.path != '':
            params['Name'] = result.path

    return params

def cred(uri: str) -> dict:
    """
    Concise synonym for the :obj:`credentials` function.

    >>> cs = cred('s3://abc:xyz:123@bucket/object.data')
    >>> for (k, v) in sorted(cs.items()):
    ...     print(k, v)
    aws_access_key_id abc
    aws_secret_access_key xyz
    aws_session_token 123
    """
    return credentials(uri)

def conf(uri: str) -> dict:
    """
    Concise synonym for the :obj:`configuration` function.

    >>> conf('s3://abc:xyz@bucket/object.data')
    {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}
    """
    return configuration(uri)

if __name__ == "__main__":
    doctest.testmod() # pragma: no cover
