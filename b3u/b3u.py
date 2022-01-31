"""
Boto3 URI utility library that supports extraction of
Boto3 configuration data from AWS resource URIs.
"""

from __future__ import annotations
import doctest
from tkinter.messagebox import NO
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
                self.Key =  result.path.lstrip('/')
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
            if not ':' in result.password:
                self.aws_secret_access_key = unquote(result.password)
                self.aws_session_token = None
            else:
                (secret, token) = result.password.split(':')
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
        self.custom_values = params

        # Extract remaining properties (custom values given by user)
        # so that they can be accessed by foo.<custom_parameter_name>
        self._extract_custom_properties(self.custom_values)


    # Extract all custom values into properties
    def _extract_custom_properties(self, params: dict):
        for key in params.keys():
            setattr(self, key, params[key])

    # Given a list of property names, creates a dictionary with structure property_name: value if value is not None
    # If safe is false, includes all custom values as well
    def _package_properties(self, property_list: list, safe: bool=True):
        result = {}

        for key_val in property_list:
            att_val = self.__getattribute__(key_val)
            if att_val is not None:
                result[key_val] = att_val
        
        if not safe:
            result.update(self.custom_values)

        return result

    def credentials(self):
        """
        Extract configuration data (only credentials) from a URI string.
        """

        return self._package_properties(['aws_access_key_id', 'aws_secret_access_key', 'aws_session_token'])
    
    def configuration(self, safe: bool=True):
        """
        Extract configuration data (both credentials and non-credentials)
        from a URI string. 
        """

        return self._package_properties(['aws_access_key_id', 'aws_secret_access_key', 'aws_session_token', 'region_name'], safe)
    
    def for_client(self, safe: bool=True):
        """
        Extract parameters for a client constructor from a URI string.
        """

        return self._package_properties(['service_name', 'region_name', 'api_version', 'endpoint_url', 'verify', 'aws_access_key_id', 'aws_secret_access_key', 'aws_session_token', 'config'], safe)

    def for_resource(self, safe: bool=True):
        """
        Extract parameters for a resource constructor from a URI string.
        This function is a synonym for the :obj:`for_client` function.
        """

        return self.for_client(safe)

    def _make_url_safe(self, uri: str) -> ParseResult:
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

    def for_get(self) -> dict:
        """
        Extract resource names from a URI for supported AWS services.
        Currently, only S3 and SSM are supported.
        """
        if self.service_name == 's3':
            return self._package_properties(['Bucket', 'Key'])
        elif self.service_name == 'ssm':
            return self._package_properties(['Name'])

        return {}
       

    def cred(self) -> dict:
        """
        Concise synonym for the :obj:`credentials` function.
        """
        return self.credentials()

    def conf(self, safe: bool=True) -> dict:
        """
        Concise synonym for the :obj:`_configuration` function.
        """
        return self.configuration(safe)

    def to_string(self) -> str:
        """
        Constructs a uri based off of whatever the current properties of this object are
        """

        new_uri = ""

        if self.service_name is not None:
            new_uri += self.service_name + "://"

        contains_aws_info = False

        if self.aws_access_key_id is not None:
            new_uri += self.aws_access_key_id

            contains_aws_info = True

        if self.aws_secret_access_key is not None:
            if contains_aws_info:
                new_uri += ":"
            else:
                contains_aws_info = True
            
            new_uri += self.aws_secret_access_key
            
        if self.aws_session_token is not None:
            if contains_aws_info:
                new_uri += ":"
            else:
                contains_aws_info = True
            
            new_uri += self.aws_session_token

        # Only include the @ if there was aws info included
        if contains_aws_info:
            new_uri += "@"
        

        if self.Bucket is not None:
            new_uri += self.Bucket

            # bucket must exist for key to exist
            if self.Key is not None:
                new_uri += "/" + self.Key
        
        elif self.Name is not None:
            new_uri += self.Name

        
        # Add in all parameters including custom values
        parameters = self._package_properties(['region_name', 'api_version', 'endpoint_url', 'verify', 'config'], False)

        first_param = True
        for key in parameters:
            if first_param:
                new_uri += "?"
                first_param = False
            else:
                new_uri += "&"
            
            new_uri += key + "=" + parameters[key]

        return new_uri

        


if __name__ == "__main__":
    doctest.testmod() # pragma: no cover

