const config = {
    namespace: "goauthentik/",
    registryTokenEndpoint: "https://ghcr.io/token",
    registryService: "ghcr.io",
};

async function getToken(event) {
    const fetch = await import("node-fetch");
    const querystring = await import("querystring");
    let scope = event.queryStringParameters["scope"];
    let tokenParams = {
        service: config.registryService,
    };
    delete event.headers.host;
    let forwardHeaders = event.headers;
    if (scope && scope.includes(":")) {
        const repo = scope.split(":")[1];
        console.debug(`oci-proxy[token]: original scope: ${scope}`);
        scope = `repository:${config.namespace}${repo}:pull`;
        console.debug(`oci-proxy[token]: rewritten scope: ${scope}`);
        tokenParams["scope"] = scope;
        // We only need to forward headers for authentication requests
        forwardHeaders = {};
    } else {
        console.debug(`oci-proxy[token]: no scope`);
        // For non-scoped requests, we need to forward some URL parameters
        ["account", "client_id", "offline_token", "token"].forEach((param) => {
            tokenParams[param] = event.queryStringParameters[param];
        });
    }
    const tokenUrl = `${config.registryTokenEndpoint}?${querystring.stringify(
        tokenParams
    )}`;
    console.debug(`oci-proxy[token]: final URL to fetch: ${tokenUrl}`);
    const tokenRes = await fetch.default(tokenUrl, {
        headers: forwardHeaders,
    });
    const tokenResult = await tokenRes.text();
    console.debug(`oci-proxy[token]: Status ${tokenRes.status}`);
    return {
        statusCode: tokenRes.status,
        body: tokenResult,
    };
}

exports.handler = async function (event, context) {
    console.debug(`oci-proxy: URL ${event.httpMethod} ${event.rawUrl}`);
    if (event.queryStringParameters.hasOwnProperty("token")) {
        console.debug("oci-proxy: handler=token proxy");
        return await getToken(event);
    }
    if (
        event.headers.authorization &&
        event.headers.authorization.startsWith("Bearer ")
    ) {
        console.debug("oci-proxy: authenticated root handler, returning 200");
        return {
            statusCode: 200,
            headers: {
                "Docker-Distribution-API-Version": "registry/2.0",
                "content-type": "application/json",
            },
            body: JSON.stringify({}),
        };
    }
    console.debug(
        "oci-proxy: root handler, returning 401 with www-authenticate"
    );
    return {
        statusCode: 401,
        headers: {
            "www-authenticate": `Bearer realm="https://${event.headers.host}/v2?token",service="${event.headers.host}",scope="repository:user/image:pull"`,
            "Docker-Distribution-API-Version": "registry/2.0",
            "content-type": "application/json",
        },
        body: JSON.stringify({}),
    };
};
