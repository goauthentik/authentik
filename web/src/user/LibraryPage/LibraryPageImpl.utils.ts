import type { Application } from "@goauthentik/api";

const isFullUrlRe = new RegExp("://");
const isHttpRe = new RegExp("http(s?)://");
const isAuthentikSpecialRe = new RegExp("goauthentik.io://");
const isNotFullUrl = (url: string) => !isFullUrlRe.test(url);
const isHttp = (url: string) => isHttpRe.test(url);
const isAuthentikSpecial = (url: string) => isAuthentikSpecialRe.test(url);

export const appHasLaunchUrl = (app: Application) => {
    const url = app.launchUrl;
    return Boolean(
        typeof url === "string" &&
            url !== "" &&
            (isHttp(url) || isNotFullUrl(url) || isAuthentikSpecial(url)),
    );
};
