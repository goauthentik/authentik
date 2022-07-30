const gitHubNamespace = "goauthentik";

exports.handler = async function (event, context) {
    let repo = "";
    if (event.path === "/") {
        repo = "/authentik";
    } else if (event.path.startsWith("/api")) {
        repo = "/client-go";
    } else {
        repo = event.path;
    }
    return {
        statusCode: 200,
        headers: {
            "content-type": "text/html",
        },
        body: `<meta name="go-import" content="${event.headers.host}${event.path} git https://github.com/${gitHubNamespace}${repo}">`,
    };
};
