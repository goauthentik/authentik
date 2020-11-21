import {
    css,
    customElement,
    html,
    LitElement,
    property,
    TemplateResult,
} from "lit-element";
// @ts-ignore
import BullseyeStyle from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
// @ts-ignore
import SpinnerStyle from "@patternfly/patternfly/components/Spinner/spinner.css";

@customElement("pb-admin-shell")
export class AdminSiteShell extends LitElement {
    @property()
    set defaultUrl(value: string) {
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
                setTimeout(() => {
                    this.loading = false;
                }, 100);
            });
    }

    render() {
        return html` ${this.loading
                ? html` <div class="pf-l-bullseye">
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
                  </div>`
                : ""}
            <slot name="body"> </slot>`;
    }
}
