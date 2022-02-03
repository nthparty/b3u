from b3u import b3u


def test_credentials():
    test_object = b3u('s3://abc:xyz@bucket/object.data')
    assert test_object.cred() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}

    test_object = b3u('s3://abc:xyz:123@bucket/object.data')
    assert test_object.cred() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz',
                                  'aws_session_token': '123'}

    test_object = b3u('s3://abc:/abcdef/ghijklmnopqrstuvwxyz/1234567890/@bucket/object.data')
    assert test_object.cred() == {'aws_access_key_id': 'abc',
                                  'aws_secret_access_key': '/abcdef/ghijklmnopqrstuvwxyz/1234567890/'}

    test_object = b3u('s3://abc:/abcdef/ghijklmnopqrstuvwxyz/1234567890/:123@bucket/object.data')
    assert test_object.cred() == {'aws_access_key_id': 'abc',
                                  'aws_secret_access_key': '/abcdef/ghijklmnopqrstuvwxyz/1234567890/',
                                  'aws_session_token': '123'}

    # Test if credentials can handle edited values
    test_object = b3u('s3://abc:xyz:123@bucket/object.data')
    test_object.aws_access_key_id = 'LMNO'
    assert test_object.cred() == {'aws_access_key_id': 'LMNO', 'aws_secret_access_key': 'xyz',
                                  'aws_session_token': '123'}


def test_configuration():
    test_object = b3u('s3://abc:xyz@bucket/object.data')
    assert test_object.conf() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}

    test_object = b3u('s3://abc:xyz:123@bucket/object.data')
    assert test_object.conf() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz',
                                  'aws_session_token': '123'}

    test_object = b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
    assert test_object.conf() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz',
                                  'region_name': 'us-east-1'}

    test_object = b3u('s3://bucket/object.data?other_param=other_value')
    assert test_object.conf(True) == {}
    assert test_object.conf(False) == {'other_param': 'other_value'}

    test_object = b3u('s3://bucket/object.data?other_param=other:value')
    assert test_object.conf(False) == {'other_param': 'other:value'}

    # Check that configuration can handle edited values
    test_object = b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
    test_object.aws_secret_access_key = '123'
    test_object.aws_session_token = '456'
    test_object.region_name = 'us-east-2'
    assert test_object.conf() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': '123',
                                  'aws_session_token': '456', 'region_name': 'us-east-2'}


def test_for_client():
    test_object = b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
    assert test_object.for_client() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz',
                                        'region_name': 'us-east-1', 'service_name': 's3'}

    """
    By default, only the parameters ``service_name``, ``region_name``,
    ``api_version``, ``endpoint_url``, ``verify``, ``aws_access_key_id``,
    ``aws_secret_access_key``, ``aws_session_token``, and ``config`` are
    extracted from the URI string.

    Other named parameters in the URI string are ignored by default, but can
    be included by setting the function parameter ``safe`` to ``False``.
    """
    test_object = b3u('s3://abc:xyz@bucket/object.data?other_param=other_value')
    assert test_object.for_client() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz',
                                        'service_name': 's3'}
    assert test_object.for_client(False) == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz',
                                             'service_name': 's3', 'other_param': 'other_value'}


def test_for_resource():
    test_object = b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
    assert test_object.for_resource() == {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz',
                                          'region_name': 'us-east-1', 'service_name': 's3'}


def test_for_get():
    test_object = b3u('s3://abc:xyz@bucket/object.data')
    assert test_object.for_get() == {'bucket': 'bucket', 'key': 'object.data'}

    test_object = b3u('ssm://ABC:XYZ@/path/to/parameter?region_name=us-east-1')
    assert test_object.for_get() == {'name': '/path/to/parameter'}

    test_object = b3u('foo://abc:xyz@bucket/object.data')
    assert test_object.for_get() == {}


def test_to_string():
    """
    The to_string method should properly reconstruct a b3u uri if any
    values have been changed
    """

    test_obj = b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1&other_param=other_value')
    assert test_obj.to_string() == 's3://abc:xyz@bucket/object.data?region_name=us-east-1&other_param=other_value'

    test_obj.region_name = "us-east-2"
    test_obj.aws_access_key_id = "LMN"
    test_obj.bucket = "new_bucket"

    assert test_obj.to_string() == 's3://LMN:xyz@new_bucket/object.data?region_name=us-east-2&other_param=other_value'

    test_object = b3u('s3://:b@bucket/object.data?region_name=us-east-1&other_param=other_value')
    assert test_object.to_string() == 's3://:b@bucket/object.data?region_name=us-east-1&other_param=other_value'

    test_object = b3u('s3://::b@bucket/object.data')
    assert test_object.to_string() == 's3://::b@bucket/object.data'

    test_object = b3u('s3://a::b@bucket/object.data')
    assert test_object.to_string() == 's3://a::b@bucket/object.data'

    test_object = b3u('s3://a::b@bucket/object.data')
    assert test_object.to_string() == 's3://a::b@bucket/object.data'

    test_object = b3u('s3://bucket/object.data')
    assert test_object.to_string() == 's3://bucket/object.data'

    test_object = b3u('ssm://ABC:XYZ@/path/to/parameter?region_name=us-east-1')
    assert test_object.to_string() == 'ssm://ABC:XYZ@/path/to/parameter?region_name=us-east-1'
    test_object.name = '/path/to/parameter2'
    assert test_object.to_string() == 'ssm://ABC:XYZ@/path/to/parameter2?region_name=us-east-1'
