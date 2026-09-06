"""
Trigger script to reproduce the dynamic structured logging anti-pattern bug (#22196).

This script generates a spoofed SAML Request XML payload with a mismatched
AssertionConsumerServiceURL (ACS URL) to test that the SAML Provider flow
correctly blocks the request and logs a structured warning without embedding
the dynamic URL in the event name.

The bug: When dynamic runtime strings were passed as the root event name in
structlog loggers, it created unbounded cardinality explosion in observability
backends (Datadog/Elasticsearch) because each unique URL generated a new event type.

IMPORTANT: You must customize the application settings below to match your
authentik instance:

1. Application slug: The slug of your SAML application as created in the authentik
   web interface (e.g., "my-saml-app", "test-app", etc.)
2. Server URL: The base URL where authentik is running (default: http://localhost:9000)
3. ACS URLs: Update both the legitimate ACS URL and the mismatched "hacker" URL
   to match your environment

Usage:
    1. Log into your authentik web interface
    2. Create a SAML Provider application and note its slug
    3. Update the variables below to match your configuration
    4. Run: `python tests/trigger_bug_reproducer.py`
    5. Check server terminal logs for the structured warning output:
       - Before fix: `[warning] ACS URL of <hacker-url> doesn't match...`
       - After fix:  `[warning] entry_invalid ... error=<exception_dict> entry=<details>`

This test helps verify the structured logging fix prevents event cardinality issues.
"""

import zlib
import base64
import urllib.parse
import urllib.request
import sys

# The slug of your SAML application as created in the authentik web interface.
# Find this in: Admin Interface → Providers → SAML → Your Application → Settings
# Example: if you created an app called "my-app", the slug would be "my-app"
application_slug = "test-bug"

# The Authentik SSO URL for your specific application
# Update this if your authentik instance runs on a different host/port
destination_url = f"http://localhost:9000/application/saml/{application_slug}/sso/binding/redirect/"

# The malicious/mismatched ACS URL that will trigger the bug
# This should be a URL that does NOT match your application's configured ACS URL
wrong_acs_url = "https://hacker.com/saml/acs"

# The legitimate ACS URL for your application (the one configured in authentik)
# Update this to match your actual application's ACS URL
legitimate_acs_url = "https://app.example.com/saml/acs"

# A minimal fake SAML request XML
saml_request_xml = f"""
<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    ID="id_12345"
                    Version="2.0"
                    IssueInstant="2026-08-14T00:00:00Z"
                    Destination="{destination_url}"
                    AssertionConsumerServiceURL="{wrong_acs_url}"
                    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>https://hacker.com</saml:Issuer>
</samlp:AuthnRequest>
"""

# SAML HTTP-Redirect binding requires "raw deflate" compression (no zlib headers)
deflate_compress = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
compressed = deflate_compress.compress(saml_request_xml.encode('utf-8')) + deflate_compress.flush()

# Base64 encode and URL encode
b64_encoded = base64.b64encode(compressed).decode('utf-8')
url_encoded = urllib.parse.quote(b64_encoded)

# Construct the final GET url
final_url = f"{destination_url}?SAMLRequest={url_encoded}"

print("Sending malicious SAML request to trigger the bug...")
print(f"URL: {final_url}\n")

try:
    req = urllib.request.Request(final_url)
    # We don't care about the response, just that it hits the server
    with urllib.request.urlopen(req) as response:
        print(f"Response Status: {response.status}")
except urllib.error.HTTPError as e:
    # 400 Bad Request is expected because the ACS URL is wrong!
    print(f"Server responded with: HTTP {e.code} {e.reason}")
    print("\nThe bug should now be triggered! Check the terminal where your server is running.")
except Exception as e:
    print(f"Connection failed: {e}")
