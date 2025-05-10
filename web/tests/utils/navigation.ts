/// <reference types="@wdio/globals/types" />

export function navigateBrowser(pathname: string = "/") {
    const nextURL = new URL(pathname, "http://localhost:9000");

    console.debug("Navigating to...", nextURL.href);

    return browser.url(nextURL.href);
}
