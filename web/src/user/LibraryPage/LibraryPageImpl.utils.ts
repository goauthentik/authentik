import type { Application } from "@goauthentik/api";

const absoluteUrl = /^[a-z][a-z\d+.-]*:\/\//i;
const supportedAbsoluteUrl = /^(?:https?|goauthentik\.io):\/\//i;

export const appHasLaunchUrl = (app: Application): boolean => {
    const url = app.launchUrl;

    return (
        typeof url === "string" &&
        url.length > 0 &&
        (!absoluteUrl.test(url) || supportedAbsoluteUrl.test(url))
    );
};
