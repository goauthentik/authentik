const gitHubNamespace = "goauthentik.io";

exports.handler = async function (event, context) {
    let repo = "";
    switch (event.path) {
        case "/":
            repo = "/authentik.git";
            break;
        case "/api":
            repo = "/client-go.git";
            break;
        default:
            repo = `${event.path}.git`;
            break;
    }
    return {
        statusCode: 200,
        headers: {
            "content-type": "text/html",
        },
        body: `<meta name="go-import" content="${event.headers.host}${event.path} git https://github.com/${gitHubNamespace}${repo}">`
    };
}
