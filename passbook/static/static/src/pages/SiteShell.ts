import { css, customElement, html, LitElement, property } from "lit-element";
// @ts-ignore
import BullseyeStyle from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
// @ts-ignore
import SpinnerStyle from "@patternfly/patternfly/components/Spinner/spinner.css";
// @ts-ignore
import BackdropStyle from "@patternfly/patternfly/components/Backdrop/backdrop.css";

@customElement("pb-site-shell")
export class SiteShell extends LitElement {
    @property()
    set url(value: string) {
        if (window.location.hash === "" && value !== undefined) {
            window.location.hash = `#${value}`;
        }
    }

    @property()
    loading: boolean = false;

    static get styles() {
        return [
            css`
                :host {
                    position: relative;
                }
                :host .pf-l-bullseye {
                    position: absolute;
                    height: 100%;
                    width: 100%;
                    top: 0;
                    left: 0;
                    z-index: 2000;
                }
            `,
            BackdropStyle,
            BullseyeStyle,
            SpinnerStyle,
        ];
    }

    constructor() {
        super();
        this.loadContent();
        window.addEventListener("hashchange", (e) => this.loadContent());
    }

    loadContent() {
        let url = window.location.hash.slice(1, Infinity);
        if (url === "") {
            return;
        }
        this.loading = true;
        fetch(url)
            .then((r) => r.text())
            .then((t) => {
                this.querySelector("[slot=body]")!.innerHTML = t;
            })
            .then(() => {
                // Ensure anchors only change the hash
                this.querySelectorAll<HTMLAnchorElement>(
                    "a:not(.pb-root-link)"
                ).forEach((a) => {
                    if (a.href === "") {
                        return;
                    }
                    try {
                        const url = new URL(a.href);
                        const qs = url.search || "";
                        a.href = `#${url.pathname}${qs}`;
                    } catch (e) {
                        a.href = `#${a.href}`;
                    }
                });
                // Create refresh buttons
                this.querySelectorAll("[role=pb-refresh]").forEach((rt) => {
                    rt.addEventListener("click", (e) => {
                        this.loadContent();
                    });
                });
                // Make get forms (search bar) notify us on submit so we can change the hash
                this.querySelectorAll("form").forEach((f) => {
                    f.addEventListener("submit", (e) => {
                        e.preventDefault();
                        const formData = new FormData(f);
                        const qs = new URLSearchParams(
                            <any>(<unknown>formData)
                        ).toString();
                        window.location.hash = `#${url}?${qs}`;
                    });
                });
                setTimeout(() => {
                    this.loading = false;
                }, 100);
            });
    }

    render() {
        return html` ${this.loading
                ? html`<div class="pf-c-backdrop">
                      <div class="pf-l-bullseye">
                          <div class="pf-l-bullseye__item">
                              <span
                                  class="pf-c-spinner pf-m-xl"
                                  role="progressbar"
                                  aria-valuetext="Loading..."
                              >
                                  <span class="pf-c-spinner__clipper"></span>
                                  <span class="pf-c-spinner__lead-ball"></span>
                                  <span class="pf-c-spinner__tail-ball"></span>
                              </span>
                          </div>
                      </div>
                  </div>`
                : ""}
            <slot name="body"> </slot>`;
    }
}
