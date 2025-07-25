import { createDocumentTemplate } from "#elements/utils/iframe";

import { TemplateResult, html } from "lit";

export interface CaptchaHandler {
    interactive(): TemplateResult;
    execute(): Promise<void>;
    refreshInteractive(): Promise<void>;
    refresh(): Promise<void>;
}

/**
 * A container iframe for a hosted Captcha, with an event emitter to monitor
 * when the Captcha forces a resize.
 *
 * Because the Captcha is itself in an iframe, the reported height is often off by some
 * margin, adding 2rem of height to our container adds padding and prevents scrollbars
 * or hidden rendering.
 */
export function iframeTemplate(children: TemplateResult, challengeURL: string): string {
    return createDocumentTemplate({
        head: html`<meta charset="UTF-8" />

            <script>
                "use strict";

                function callback(token) {
                    self.parent.postMessage({
                        message: "captcha",
                        source: "goauthentik.io",
                        context: "flow-executor",
                        token,
                    });
                }

                function loadListener() {
                    self.parent.postMessage({
                        message: "load",
                        source: "goauthentik.io",
                        context: "flow-executor",
                    });
                }
            </script>

            <style>
                body {
                    margin: 0;
                    padding: 0;
                }

                .g-recaptcha {
                    padding-block: 0.5rem;
                }

                .g-recaptcha,
                .h-captcha {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
            </style>`,
        body: html`${children}
            <script onload="loadListener()" src="${challengeURL}"></script> `,
    });
}
