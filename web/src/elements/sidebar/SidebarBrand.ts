import { tenant } from "@goauthentik/common/api/config";
import { EVENT_SIDEBAR_TOGGLE } from "@goauthentik/common/constants";
import { configureSentry } from "@goauthentik/common/sentry";
import { first } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGlobal from "@patternfly/patternfly/patternfly-base.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CurrentTenant } from "@goauthentik/api";

// If the viewport is wider than MIN_WIDTH, the sidebar
// is shown besides the content, and not overlaid.
export const MIN_WIDTH = 1200;

export const DefaultTenant: CurrentTenant = {
    brandingLogo: "/static/dist/assets/icons/icon_left_brand.svg",
    brandingFavicon: "/static/dist/assets/icons/icon.png",
    brandingTitle: "authentik",
    uiFooterLinks: [],
    matchedDomain: "",
    defaultLocale: "",
};

@customElement("ak-sidebar-brand")
export class SidebarBrand extends AKElement {
    @property({ attribute: false })
    tenant: CurrentTenant = DefaultTenant;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFGlobal,
            PFPage,
            PFButton,
            css`
                :host {
                    display: flex;
                    flex-direction: row;
                    align-items: center;
                    height: 114px;
                    min-height: 114px;
                }
                .pf-c-brand img {
                    width: 100%;
                    padding: 0 0.5rem;
                    height: 42px;
                }
                button.pf-c-button.sidebar-trigger {
                    background-color: transparent;
                    border-radius: 0px;
                    height: 100%;
                    color: var(--ak-dark-foreground);
                }
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener("resize", () => {
            this.requestUpdate();
        });
    }

    firstUpdated(): void {
        configureSentry(true);
        tenant().then((tenant) => (this.tenant = tenant));
    }

    render(): TemplateResult {
        return html` ${window.innerWidth <= MIN_WIDTH
                ? html`
                      <button
                          class="sidebar-trigger pf-c-button"
                          @click=${() => {
                              this.dispatchEvent(
                                  new CustomEvent(EVENT_SIDEBAR_TOGGLE, {
                                      bubbles: true,
                                      composed: true,
                                  }),
                              );
                          }}
                      >
                          <i class="fas fa-bars"></i>
                      </button>
                  `
                : html``}
            <a href="#/" class="pf-c-page__header-brand-link">
                <div class="pf-c-brand ak-brand">
                    <img
                        src="${first(this.tenant.brandingLogo, DefaultTenant.brandingLogo)}"
                        alt="authentik Logo"
                        loading="lazy"
                    />
                </div>
            </a>`;
    }
}
