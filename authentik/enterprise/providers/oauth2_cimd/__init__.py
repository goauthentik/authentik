"""OAuth Client ID Metadata Document (CIMD) support, public clients.

Implements draft-ietf-oauth-client-id-metadata-document-03 for public clients
(`none` authentication, authorization code). Entry points:

- `resolver.resolve_public_client(client_id, *, admit)` and `resolver.invalidate(client_id)`
- `client.CIMDClient`, the picklable result
- `metadata.redirect_uri_allowed(registered, presented)` and `metadata.parse_client_id()`
- `errors.CIMDError` and its subclasses"""
