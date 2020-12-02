import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import BullseyeStyle from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
// @ts-ignore
import SpinnerStyle from "@patternfly/patternfly/components/Spinner/spinner.css";
// @ts-ignore
import BackdropStyle from "@patternfly/patternfly/components/Backdrop/backdrop.css";
import { SpinnerSize } from "../../elements/Spinner";

@customElement("pb-site-shell")
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
                :host .pf-l-bullseye {
                    position: absolute;
                    height: 100%;
                    width: 100%;
                    top: 0;
                    left: 0;
                    z-index: 2000;
                }
                .pf-c-backdrop {
                    --pf-c-backdrop--BackgroundColor: rgba(0, 0, 0, 0) !important;
                }
            `,
            BackdropStyle,
            BullseyeStyle,
            SpinnerStyle,
        ];
    }

    loadContent(): void {
        if (!this._url) {
            return;
        }
        this.loading = true;
        fetch(this._url)
            .then((r) => {
                if (r.ok) {
                    return r;
                }
                console.debug(`passbook/site-shell: Request failed ${this._url}`);
                window.location.hash = "#/";
                throw new Error("Request failed");
            })
            .then((r) => r.text())
            .then((t) => {
                const bodySlot = this.querySelector("[slot=body]");
                if (!bodySlot) {
                    return;
                }
                bodySlot.innerHTML = t;
            })
            .then(() => {
                // Ensure anchors only change the hash
                this.querySelectorAll<HTMLAnchorElement>("a:not(.pb-root-link)").forEach((a) => {
                    if (a.href === "") {
                        return;
                    }
                    try {
                        const url = new URL(a.href);
                        const qs = url.search || "";
                        a.href = `#${url.pathname}${qs}`;
                    } catch (e) {
                        console.debug(`passbook/site-shell: error ${e}`);
                        a.href = `#${a.href}`;
                    }
                });
                // Create refresh buttons
                this.querySelectorAll("[role=pb-refresh]").forEach((rt) => {
                    rt.addEventListener("click", () => {
                        this.loadContent();
                    });
                });
                // Make get forms (search bar) notify us on submit so we can change the hash
                this.querySelectorAll("form").forEach((f) => {
                    f.addEventListener("submit", (e) => {
                        e.preventDefault();
                        const formData = new FormData(f);
                        const qs = new URLSearchParams((<any>formData)).toString(); // eslint-disable-line
                        window.location.hash = `#${this._url}?${qs}`;
                    });
                });
                setTimeout(() => {
                    this.loading = false;
                }, 100);
            });
    }

    render(): TemplateResult {
        return html` ${this.loading ?
            html`<div class="pf-c-backdrop">
                    <div class="pf-l-bullseye">
                        <div class="pf-l-bullseye__item">
                            <pb-spinner size=${SpinnerSize.Large}></pb-spinner>
                        </div>
                    </div>
                </div>`
            : ""}
            <slot name="body"></slot>`;
    }
}
