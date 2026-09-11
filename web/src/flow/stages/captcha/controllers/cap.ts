import { CaptchaController } from "#flow/stages/captcha/controllers/CaptchaController";

import { html } from "lit";

export function isCapWidgetURL(url: URL): boolean {
    return url.pathname.includes("cap-widget") || url.pathname.endsWith("/assets/widget.js");
}

export class CapController extends CaptchaController {
    public static readonly globalName = "cap-widget";

    public static readonly scriptType = "module";

    public static override isAvailable(): boolean {
        return customElements.get("cap-widget") !== undefined;
    }

    public static override matchesURL(url: URL): boolean {
        return isCapWidgetURL(url);
    }

    public interactive = () => {
        const endpoint = this.host.challenge?.siteKey ?? "";

        return html`<div id="ak-container" class="cap-container">
                <cap-widget
                    id="ak-cap-widget"
                    required
                    data-cap-api-endpoint=${endpoint}
                ></cap-widget>
            </div>
            <script>
                const widget = document.getElementById("ak-cap-widget");

                widget.addEventListener("solve", (event) => {
                    callback(event.detail.token);
                });

                widget.addEventListener("error", (event) => {
                    self.parent.postMessage({
                        message: "error",
                        source: "goauthentik.io",
                        context: "flow-executor",
                        error: event.detail.message,
                    });
                });
            </script>`;
    };

    public refreshInteractive = async () => {
        this.host.iframeRef.value?.contentWindow?.location.reload();
    };

    public execute = async () => {
        throw new Error("Cap requires interactive mode.");
    };

    public refresh = async () => {
        throw new Error("Cap requires interactive mode.");
    };
}
