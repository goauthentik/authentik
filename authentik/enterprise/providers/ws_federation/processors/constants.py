from authentik.sources.saml.processors.constants import NS_MAP as _map

WS_FED_ACTION_SIGN_IN = "wsignin1.0"
WS_FED_ACTION_SIGN_OUT = "wsignout1.0"

WS_FED_POST_KEY_ACTION = "wa"
WS_FED_POST_KEY_RESULT = "wresult"
WS_FED_POST_KEY_CONTEXT = "wctx"

NS_WS_FED_PROTOCOL = "http://docs.oasis-open.org/wsfed/federation/200706"
NS_WSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_ADDRESSING = "http://www.w3.org/2005/08/addressing"

NS_MAP = {
    **_map,
    "fed": NS_WS_FED_PROTOCOL,
    "xsi": NS_WSI,
    "wsa": NS_ADDRESSING,
}
