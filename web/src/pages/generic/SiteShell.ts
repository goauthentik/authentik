import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { SpinnerSize } from "../../elements/Spinner";
import { showMessage } from "../../elements/messages/MessageContainer";
import { gettext } from "django";
import { SentryIgnoredError } from "../../common/errors";
import { unsafeHTML } from "lit-html/directives/unsafe-html";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";

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

    @property({type: String})
    body = "";

    static get styles(): CSSResult[] {
        return [PFPage, PFGallery, PFContent].concat(
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
            `
        );
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
            .then((response) => {
                if (response.ok) {
                    return response;
                }
                console.debug(`authentik/site-shell: Request failed ${this._url}`);
                window.location.hash = "#/";
                showMessage({
                    level_tag: "error",
                    message: gettext(`Request failed: ${response.statusText}`),
                });
                this.loading = false;
                throw new SentryIgnoredError("Request failed");
            })
            .then((response) => response.text())
            .then((text) => {
                this.body = text;
            })
            .then(() => {
                setTimeout(() => {
                    this.loading = false;
                }, 100);
            });
    }

    updateHandlers(): void {
        // Ensure anchors only change the hash
        this.shadowRoot?.querySelectorAll<HTMLAnchorElement>("a:not(.ak-root-link)").forEach((a) => {
            if (a.href === "") {
                return;
            }
            if (a.href.startsWith("#")) {
                return;
            }
            try {
                const url = new URL(a.href);
                const qs = url.search || "";
                const hash = (url.hash || "#").substring(2, Infinity);
                a.href = `#${url.pathname}${qs}${hash}`;
            } catch (e) {
                console.debug(`authentik/site-shell: error ${e}`);
                a.href = `#${a.href}`;
            }
        });
        // Create refresh buttons
        this.shadowRoot?.querySelectorAll("[role=ak-refresh]").forEach((rt) => {
            rt.addEventListener("click", () => {
                this.loadContent();
            });
        });
        // Make get forms (search bar) notify us on submit so we can change the hash
        this.shadowRoot?.querySelectorAll<HTMLFormElement>("form[method=get]").forEach((form) => {
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const qs = new URLSearchParams((<any>formData)).toString(); // eslint-disable-line
                window.location.hash = `#${this._url}?${qs}`;
            });
        });
        // Make forms with POST Method have a correct action set
        this.shadowRoot?.querySelectorAll<HTMLFormElement>("form[method=post]").forEach((form) => {
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
                        this.body = data;
                        this.updateHandlers();
                    })
                    .catch((e) => {
                        showMessage({
                            level_tag: "error",
                            message: "Unexpected error"
                        });
                        console.error(e);
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
            ${unsafeHTML(this.body)}`;
    }

    updated(): void {
        this.updateHandlers();
    }
}
