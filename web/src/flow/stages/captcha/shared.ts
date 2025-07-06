import { TemplateResult, html } from "lit";

export interface CaptchaHandler {
    interactive(): Promise<unknown>;
    execute(): Promise<unknown>;
    refreshInteractive(): Promise<unknown>;
    refresh(): Promise<unknown>;
}

/**
 * A container iframe for a hosted Captcha, with an event emitter to monitor
 * when the Captcha forces a resize.
 *
 * Because the Captcha is itself in an iframe, the reported height is often off by some
 * margin, adding 2rem of height to our container adds padding and prevents scrollbars
 * or hidden rendering.
 */
export function iframeTemplate(children: TemplateResult, challengeURL: string): TemplateResult {
    return html` ${children}
        <script>
            new ResizeObserver((entries) => {
                const height =
                    document.body.offsetHeight +
                    parseFloat(getComputedStyle(document.body).fontSize) * 2;

                self.parent.postMessage({
                    message: "resize",
                    source: "goauthentik.io",
                    context: "flow-executor",
                    size: { height },
                });
            }).observe(document.querySelector(".ak-captcha-container"));
        </script>

        <script src=${challengeURL}></script>

        <script>
            function callback(token) {
                self.parent.postMessage({
                    message: "captcha",
                    source: "goauthentik.io",
                    context: "flow-executor",
                    token,
                });
            }
        </script>`;
}
