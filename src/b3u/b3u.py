"""
Boto3 URI utility library that supports extraction of
Boto3 configuration data from AWS resource URIs.
"""
from __future__ import annotations
import doctest
from urllib.parse import urlparse, parse_qs, quote, unquote, ParseResult


class b3u:

    def __init__(self, uri: str):

        result = self._make_url_safe(uri)

        self.Bucket = None
        self.Key = None
        self.Name = None

        if result.scheme == 's3':
            if result.hostname is not None and result.hostname != '':
                self.Bucket = result.hostname
            if result.path is not None and result.path != '':
                self.Key = result.path.lstrip('/')
        elif result.scheme == 'ssm':
            if result.path is not None and result.path != '':
                self.Name = result.path

        params = {}
        result = self._make_url_safe(uri)

        if result.username is not None and result.username != '':
            self.aws_access_key_id = result.username
        else:
            self.aws_access_key_id = None

        if result.password is not None and result.password != '':
            if ':' not in result.password:
                self.aws_secret_access_key = unquote(result.password)
                self.aws_session_token = None
            else:
                (secret, token) = result.password.split(':')
                # Secret key not provided, but token is: 'abc::token@...'
                if secret == '':
                    self.aws_secret_access_key = None
                else:
                    self.aws_secret_access_key = unquote(secret)
                self.aws_session_token = token
        else:
            self.aws_secret_access_key = None
            self.aws_session_token = None

        result = parse_qs(self._make_url_safe(uri).query)

        for (key, values) in result.items():
            if len(values) == 1:
                params[key] = values[0]

        result = self._make_url_safe(uri)
        self.service_name = result.scheme

        # Extract remaining default/'safe' properties from params
        # so that all that remains is custom values
        self.region_name = params.pop('region_name', None)
        self.api_version = params.pop('api_version', None)
        self.endpoint_url = params.pop('endpoint_url', None)
        self.verify = params.pop('verify', None)
        self.config = params.pop('config', None)

        # Only values left in params should be custom user values
        self.custom_values = params.keys()

        # Extract remaining properties (custom values given by user)
        # so that they can be accessed by foo.<custom_parameter_name>
        self._extract_custom_properties(params)

    # Extract all custom values into properties
    def _extract_custom_properties(self, params: dict):
        for key in params.keys():
            setattr(self, key, params[key])

    # Get current values of all originally entered custom values
    def _get_custom_values(self):
        r = {}

        for custom_key in self.custom_values:
            r[custom_key] = getattr(self, custom_key)

        return r

    # Given a list of property names, creates a dictionary with structure property_name: value if value is not None
    # If safe is false, includes all custom values as well
    def _package_properties(self, property_list: list, safe: bool = True) -> dict:
        result = {}

        for key_val in property_list:
            att_val = self.__getattribute__(key_val)
            if att_val is not None:
                result[key_val] = att_val

        if not safe:
            result.update(self._get_custom_values())

        return result

    def credentials(self) -> dict:
        """
        Extract configuration data (only credentials) from a URI string.

        >>> b3u('s3://abc:xyz@bucket/object.data').credentials()
        {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}

        The format ``abc:xyz:123`` can be used to specify a session
        token (which is the third component, ``123``, in this example)
        as part of a URI.

        >>> cs = b3u('s3://abc:xyz:123@bucket/object.data').credentials()
        >>> for (k, v) in sorted(cs.items()):
        ...     print(k, v)
        aws_access_key_id abc
        aws_secret_access_key xyz
        aws_session_token 123

        If the aws_secret_access_key contains a slash, it should not be escaped or URL encoded.

        :return: A dictionary with the following keys (if available):
            aws_access_key_id, aws_secret_access_key, aws_session_token
        """

        return self._package_properties(['aws_access_key_id', 'aws_secret_access_key', 'aws_session_token'])

    def configuration(self, safe: bool = True) -> dict:
        """
        Extract configuration data (both credentials and non-credentials)
        from a URI string.

        :param safe: If true, only return standard AWS properties that can be passed to.
            If false, returns all.

        >>> b3u('s3://abc:xyz@bucket/object.data?other_param=other_value').configuration()
        {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}

        >>> b3u('s3://abc:xyz@bucket/object.data?other_param=other_value').configuration(False)
        {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz', 'other_param': 'other_value'}

        """

        return self._package_properties(
            ['aws_access_key_id', 'aws_secret_access_key', 'aws_session_token', 'region_name'], safe)

    def for_client(self, safe: bool = True) -> dict:
        """
        Extract parameters for a client constructor from a URI string.

        :param safe: If true, only return standard AWS properties that can be passed to.
            If false, return all.

        >>> ps = b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1').for_client()
        >>> for (k, v) in sorted(ps.items()):
        ...     print(k, v)
        aws_access_key_id abc
        aws_secret_access_key xyz
        region_name us-east-1
        service_name s3

        >>> ps = b3u('s3://abc:xyz@bucket/object.data?other_param=other_value').for_client(False)
        >>> for (k, v) in sorted(ps.items()):
        ...     print(k, v)
        aws_access_key_id abc
        aws_secret_access_key xyz
        other_param other_value
        service_name s3

        """

        return self._package_properties(
            ['service_name', 'region_name', 'api_version', 'endpoint_url', 'verify', 'aws_access_key_id',
             'aws_secret_access_key', 'aws_session_token', 'config'], safe)

    def for_resource(self, safe: bool = True) -> dict:
        """
        Extract parameters for a resource constructor from a URI string.
        This function is a synonym for the :obj:`for_client` function.

        :param safe: If true, only return standard AWS properties that can be passed to. If false, returns all

        >>> ps = b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1').for_resource()
        >>> for (k, v) in sorted(ps.items()):
        ...     print(k, v)
        aws_access_key_id abc
        aws_secret_access_key xyz
        region_name us-east-1
        service_name s3
        """

        return self.for_client(safe)

    def _make_url_safe(self, uri: str) -> ParseResult:
        """
        URL encode slashes in ``aws_secret_access_key`` to ensure compatibility
        with ``urlparse``.

        :param uri: AWS resource URI
        :return: URL parsed URI with slashes in ``aws_secret_access_key`` encoded
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

    def for_get(self) -> dict:
        """
        Extract resource names from a URI for supported AWS services.
        Currently, only S3 and SSM are supported.

        >>> b3u('s3://abc:xyz@bucket/object.data').for_get()
        {'Bucket': 'bucket', 'Key': 'object.data'}

        >>> b3u('ssm://ABC:XYZ@/path/to/parameter?region_name=us-east-1').for_get()
        {'Name': '/path/to/parameter'}
        """
        if self.service_name == 's3':
            return self._package_properties(['Bucket', 'Key'])
        elif self.service_name == 'ssm':
            return self._package_properties(['Name'])

        return {}

    def cred(self) -> dict:
        """
        Concise synonym for the :obj:`credentials` function.

        >>> cs = b3u('s3://abc:xyz:123@bucket/object.data').cred()
        >>> for (k, v) in sorted(cs.items()):
        ...     print(k, v)
        aws_access_key_id abc
        aws_secret_access_key xyz
        aws_session_token 123

        """
        return self.credentials()

    def conf(self, safe: bool = True) -> dict:
        """
        Concise synonym for the :obj:`_configuration` function.

        >>> b3u('s3://abc:xyz@bucket/object.data').conf()
        {'aws_access_key_id': 'abc', 'aws_secret_access_key': 'xyz'}

        """
        return self.configuration(safe)

    def to_string(self) -> str:
        """
        Constructs a uri based off of whatever the current properties of this object are

        >>> b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1').to_string()
        's3://abc:xyz@bucket/object.data?region_name=us-east-1'

        >>> b = b3u('s3://abc:xyz@bucket/object.data?region_name=us-east-1')
        >>> b.aws_access_key_id = 'LMN'
        >>> b.to_string()
        's3://LMN:xyz@bucket/object.data?region_name=us-east-1'
        """

        new_uri = ''

        if self.service_name is not None:
            new_uri += self.service_name + '://'

        contains_aws_info = False

        if self.aws_access_key_id is not None:
            new_uri += self.aws_access_key_id
            contains_aws_info = True

        if self.aws_secret_access_key is not None:
            contains_aws_info = True
            new_uri += ':' + self.aws_secret_access_key

        if self.aws_session_token is not None:
            contains_aws_info = True
            if self.aws_secret_access_key is None:
                new_uri += ':'

            new_uri += ':' + self.aws_session_token

        # Only include the @ if there was aws info included
        if contains_aws_info:
            new_uri += '@'

        if self.Bucket is not None:
            new_uri += self.Bucket

            # bucket must exist for key to exist
            if self.Key is not None:
                new_uri += '/' + self.Key

        elif self.Name is not None:
            new_uri += self.Name

        # Add in all parameters including custom values
        parameters = self._package_properties(
            ['region_name', 'api_version', 'endpoint_url', 'verify', 'config'], False)

        first_param = True
        for key in parameters:
            if first_param:
                new_uri += '?'
                first_param = False
            else:
                new_uri += '&'

            new_uri += key + '=' + parameters[key]

        return new_uri


if __name__ == "__main__":
    doctest.testmod()  # pragma: no cover
