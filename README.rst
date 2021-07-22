===
b3u
===

Boto3 URI utility library that supports extraction of Boto3 configuration data from AWS resource URIs.

|pypi| |travis| |coveralls|

.. |pypi| image:: https://badge.fury.io/py/b3u.svg
   :target: https://badge.fury.io/py/b3u
   :alt: PyPI version and link.

.. |travis| image:: https://travis-ci.com/nthparty/b3u.svg?branch=main
   :target: https://travis-ci.com/nthparty/b3u

.. |coveralls| image:: https://coveralls.io/repos/github/nthparty/blooms/badge.svg?branch=main
   :target: https://coveralls.io/github/nthparty/b3u?branch=main

Purpose
-------
When applications that employ `Boto3 <https://boto3.readthedocs.io>`_ must work with AWS resources that are spread across multiple accounts, it can be useful to tie AWS configuration information (both `credentials <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html>`_ and `non-credentials <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html>`_) directly to associated AWS resources (*e.g.*, by including the configuration data within URIs). This library provides methods that extract AWS configuration data from URIs, offering a succinct syntax for passing (directly into boto3 methods) configuration data that is included within URIs.

Package Installation and Usage
------------------------------
The package is available on PyPI::

    python -m pip install b3u

The library can be imported in the usual ways::

    import b3u
    from b3u import *

The library provides methods for extracting configuration data (credentials and non-credentials) from URIs, as in the examples below::

    # Create an S3 client given a URI (for an object in an S3 bucket) that
    # includes credentials (an access key `ABC` and a secret key `XYZ`).
    boto3.client('s3', **b3u.cred("s3://ABC:XYZ@example-bucket/object.data"))

    # Create an S3 client given a URI (for an S3 bucket) that includes
    # credentials (an access key `ABC`, a secret key `XYZ`, and a session
    # token `UVW`).
    boto3.client('s3', **b3u.cred("s3://ABC:XYZ:UVW@example-bucket"))

    # Create an SSM client given a URI (naming a particular a parameter in
    # the Parameter Store) that specifies the AWS Region `us-east-1`.
    boto3.client('ssm', **b3u.conf("ssm://ABC:XYZ@/path/to/parameter?region_name=us-east-1"))

    # Create an SSM client given a URI that contains no credentials but
    # does specify an AWS Region. Since no credentials are present in the
    # URI, the boto3 library will look for them in other locations in the
    # manner specified in the Boto3 documentation).
    boto3.client('ssm', **b3u.conf("ssm:///path/to/parameter?region_name=us-east-1"))

Testing and Conventions
-----------------------
All unit tests are executed and their coverage is measured when using `nose <https://nose.readthedocs.io/>`_ (see ``setup.cfg`` for configution details)::

    nosetests

Alternatively, all unit tests are included in the module itself and can be executed using `doctest <https://docs.python.org/3/library/doctest.html>`_::

    python b3u/b3u.py -v

Style conventions are enforced using `Pylint <https://www.pylint.org/>`_::

    pylint b3u

Contributions
-------------
In order to contribute to the source code, open an issue or submit a pull request on the GitHub page for this library.

Versioning
----------
The version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`_.
