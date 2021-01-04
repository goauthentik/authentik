import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import BullseyeStyle from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
// @ts-ignore
import SpinnerStyle from "@patternfly/patternfly/components/Spinner/spinner.css";
// @ts-ignore
import BackdropStyle from "@patternfly/patternfly/components/Backdrop/backdrop.css";
import { SpinnerSize } from "../../elements/Spinner";
import { showMessage } from "../../elements/messages/MessageContainer";
import { gettext } from "django";
import { SentryIgnoredError } from "../../common/errors";

@customElement("ak-site-shell")
export class SiteShell extends LitElement {
    @property()
    set url(value: string) {
        this._url = value;
        this.loadContent();
    }

    _url?: string;

    @property({type: Boolean})
    loading = false;

    static get styles(): CSSResult[] {
        return [
            css`
                :host,
                ::slotted(*) {
                    height: 100%;
                }
                .pf-l-bullseye {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                }
            `,
            BackdropStyle,
            BullseyeStyle,
            SpinnerStyle,
        ];
    }

    constructor() {
        super();
        this.addEventListener("ak-refresh", () => {
            this.loadContent();
        });
    }

    loadContent(): void {
        const bodySlot = this.querySelector("[slot=body]");
        if (!bodySlot) {
            return;
        }
        if (!this._url) {
            return;
        }
        if (this.loading) {
            return;
        }
        this.loading = true;
        fetch(this._url)
            .then((r) => {
                if (r.ok) {
                    return r;
                }
                console.debug(`authentik/site-shell: Request failed ${this._url}`);
                window.location.hash = "#/";
                showMessage({
                    level_tag: "error",
                    message: gettext(`Request failed: ${r.statusText}`),
                });
                this.loading = false;
                throw new SentryIgnoredError("Request failed");
            })
            .then((r) => r.text())
            .then((text) => {
                bodySlot.innerHTML = text;
                this.updateHandlers();
            })
            .then(() => {
                setTimeout(() => {
                    this.loading = false;
                }, 100);
            });
    }

    updateHandlers(): void {
        // Ensure anchors only change the hash
        this.querySelectorAll<HTMLAnchorElement>("a:not(.ak-root-link)").forEach((a) => {
            if (a.href === "") {
                return;
            }
            try {
                const url = new URL(a.href);
                const qs = url.search || "";
                a.href = `#${url.pathname}${qs}`;
            } catch (e) {
                console.debug(`authentik/site-shell: error ${e}`);
                a.href = `#${a.href}`;
            }
        });
        // Create refresh buttons
        this.querySelectorAll("[role=ak-refresh]").forEach((rt) => {
            rt.addEventListener("click", () => {
                this.loadContent();
            });
        });
        // Make get forms (search bar) notify us on submit so we can change the hash
        this.querySelectorAll<HTMLFormElement>("form[method=get]").forEach((form) => {
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const qs = new URLSearchParams((<any>formData)).toString(); // eslint-disable-line
                window.location.hash = `#${this._url}?${qs}`;
            });
        });
        // Make forms with POST Method have a correct action set
        this.querySelectorAll<HTMLFormElement>("form[method=post]").forEach((form) => {
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                fetch(this._url ? this._url : form.action, {
                    method: form.method,
                    body: formData,
                })
                    .then((response) => {
                        return response.text();
                    })
                    .then((data) => {
                        const bodySlot = this.querySelector("[slot=body]");
                        if (!bodySlot) {
                            return;
                        }
                        bodySlot.innerHTML = data;
                        this.updateHandlers();
                    })
                    .catch((e) => {
                        showMessage({
                            level_tag: "error",
                            message: "Unexpected error"
                        });
                        console.log(e);
                    });
            });
        });
    }

    render(): TemplateResult {
        return html` ${this.loading ?
            html`<div class="pf-l-bullseye">
                    <div class="pf-l-bullseye__item">
                        <ak-spinner size=${SpinnerSize.XLarge}></ak-spinner>
                    </div>
                </div>`
            : ""}
            <slot name="body"></slot>`;
    }
}
