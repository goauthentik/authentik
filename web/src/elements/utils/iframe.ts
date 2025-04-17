/**
 * @file IFrame Utilities
 */

interface IFrameLoadResult {
    contentWindow: Window;
    contentDocument: Document;
}

export function pluckIFrameContent(iframe: HTMLIFrameElement) {
    const contentWindow = iframe.contentWindow;
    const contentDocument = iframe.contentDocument;

    if (!contentWindow) {
        throw new Error("Iframe contentWindow is not accessible");
    }

    if (!contentDocument) {
        throw new Error("Iframe contentDocument is not accessible");
    }

    return {
        contentWindow,
        contentDocument,
    };
}

export function resolveIFrameContent(iframe: HTMLIFrameElement): Promise<IFrameLoadResult> {
    if (iframe.contentDocument?.readyState === "complete") {
        return Promise.resolve(pluckIFrameContent(iframe));
    }

    return new Promise((resolve) => {
        iframe.addEventListener("load", () => resolve(pluckIFrameContent(iframe)), { once: true });
    });
}

/**
 * Creates a minimal HTML wrapper for an iframe.
 *
 * @deprecated Use the `contentDocument.body` directly instead.
 */
export function createIFrameHTMLWrapper(bodyContent: string): string {
    const html = String.raw;

    return html`<!doctype html>
        <html>
            <head>
                <meta charset="utf-8" />
            </head>
            <body style="display:flex;flex-direction:row;justify-content:center;">
                ${bodyContent}
            </body>
        </html>`;
}
