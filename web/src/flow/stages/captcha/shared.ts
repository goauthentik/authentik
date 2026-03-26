import type { ResolvedUITheme } from "#common/theme";

import { createDocumentTemplate } from "#elements/utils/iframe";

import { html, TemplateResult } from "lit";

const ThemeColor = {
    dark: "#18191a",
    light: "#ffffff",
} as const satisfies Record<ResolvedUITheme, string>;

export function themeMeta(theme: ResolvedUITheme) {
    switch (theme) {
        case "dark":
            return html`
                <meta name="color-scheme" content="dark" />
                <meta name="theme-color" content=${ThemeColor.dark} />
            `;
        case "light":
            return html` <meta name="color-scheme" content="light" />
                <meta name="theme-color" content=${ThemeColor.light} />`;
    }
}

export interface IFrameTemplateInit {
    challengeURL: URL | string;
    theme: ResolvedUITheme;
}

/**
 * A container iframe for a hosted Captcha, with an event emitter to monitor
 * when the Captcha forces a resize.
 *
 * Because the Captcha is itself in an iframe, the reported height is often off by some
 * margin, adding 2rem of height to our container adds padding and prevents scrollbars
 * or hidden rendering.
 */
export function iframeTemplate(
    children: TemplateResult,
    { challengeURL, theme }: IFrameTemplateInit,
) {
    return createDocumentTemplate({
        head: html`
            <meta charset="UTF-8" />

            ${themeMeta(theme)}
        `,
        body: html`
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
                html,
                body {
                    background: ${ThemeColor[theme]};
                }

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
            </style>
            ${children}
            <script onload="loadListener()" src="${challengeURL.toString()}"></script>
        `,
    });
}
