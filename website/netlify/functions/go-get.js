const gitHubNamespace = "goauthentik";

exports.handler = async function (event, context) {
    let repo = "";
    if (event.path.startsWith("/api")) {
        repo = "client-go";
    } else if (event.path.startsWith("/terraform-provider-authentik")) {
        repo = "terraform-provider-authentik";
    } else {
        repo = "authentik";
    }
    return {
        statusCode: 200,
        headers: {
            "content-type": "text/html",
        },
        body: `<meta name="go-import" content="${event.headers.host}${event.path} git https://github.com/${gitHubNamespace}/${repo}">`,
    };
};
