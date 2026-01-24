from authentik.sources.saml.processors.constants import NS_MAP as _map

WS_FED_ACTION_SIGN_IN = "wsignin1.0"
WS_FED_ACTION_SIGN_OUT = "wsignout1.0"
WS_FED_ACTION_SIGN_OUT_CLEANUP = "wsignoutcleanup1.0"

WS_FED_POST_KEY_ACTION = "wa"
WS_FED_POST_KEY_RESULT = "wresult"
WS_FED_POST_KEY_CONTEXT = "wctx"

WSS_TOKEN_TYPE_SAML2 = (
    "http://docs.oasis-open.org/wss/oasis-wss-saml-token-profile-1.1#SAMLV2.0"  # nosec
)
WSS_KEY_IDENTIFIER_SAML_ID = (
    "http://docs.oasis-open.org/wss/oasis-wss-saml-token-profile-1.1#SAMLID"
)

NS_WS_FED_PROTOCOL = "http://docs.oasis-open.org/wsfed/federation/200706"
NS_WS_FED_TRUST = "http://schemas.xmlsoap.org/ws/2005/02/trust"
NS_WSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_ADDRESSING = "http://www.w3.org/2005/08/addressing"
NS_POLICY = "http://schemas.xmlsoap.org/ws/2004/09/policy"
NS_WSS_SEC = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
NS_WSS_UTILITY = (
    "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
)
NS_WSS_D3P1 = "http://docs.oasis-open.org/wss/oasis-wss-wssecurity-secext-1.1.xsd"

NS_MAP = {
    **_map,
    "fed": NS_WS_FED_PROTOCOL,
    "xsi": NS_WSI,
    "wsa": NS_ADDRESSING,
    "t": NS_WS_FED_TRUST,
    "wsu": NS_WSS_UTILITY,
    "wsp": NS_POLICY,
    "wssec": NS_WSS_SEC,
    "d3p1": NS_WSS_D3P1,
}
