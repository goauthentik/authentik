GitHub Auth for Sentry
======================

An SSO provider for Sentry which enables GitHub organization-restricted authentication.

Install
-------

::

    $ pip install https://github.com/getsentry/sentry-auth-github/archive/master.zip

Setup
-----

Create a new application under your organization in GitHub. Enter the **Authorization
callback URL** as the prefix to your Sentry installation:

::

    https://example.sentry.com


Once done, grab your API keys and drop them in your ``sentry.conf.py``:

.. code-block:: python

    GITHUB_APP_ID = ""

    GITHUB_API_SECRET = ""


Verified email addresses can optionally be required:

.. code-block:: python

    GITHUB_REQUIRE_VERIFIED_EMAIL = True


Optionally you may also specify the domain (for GHE users):

.. code-block:: python

    GITHUB_BASE_DOMAIN = "git.example.com"

    GITHUB_API_DOMAIN = "api.git.example.com"


If Subdomain isolation is disabled in GHE:

.. code-block:: python

    GITHUB_BASE_DOMAIN = "git.example.com"

    GITHUB_API_DOMAIN = "git.example.com/api/v3"
