import { AKElement } from "@goauthentik/elements/Base";
import { WithBrandConfig } from "@goauthentik/elements/mixins/brand";
import { themeImage } from "@goauthentik/elements/utils/images";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGlobal from "@patternfly/patternfly/patternfly-base.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CurrentBrand, UiThemeEnum } from "@goauthentik/api";

// If the viewport is wider than MIN_WIDTH, the sidebar
// is shown besides the content, and not overlaid.
export const MIN_WIDTH = 1200;

export const DefaultBrand: CurrentBrand = {
    brandingLogo: "/static/dist/assets/icons/icon_left_brand.svg",
    brandingFavicon: "/static/dist/assets/icons/icon.png",
    brandingTitle: "authentik",
    brandingCustomCss: "",
    uiFooterLinks: [],
    uiTheme: UiThemeEnum.Automatic,
    matchedDomain: "",
    defaultLocale: "",
};

@customElement("ak-sidebar-brand")
export class SidebarBrand extends WithBrandConfig(AKElement) {
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
                    height: var(--ak-navbar-height);
                    border-bottom: var(--pf-global--BorderWidth--sm);
                    border-bottom-style: solid;
                    border-bottom-color: var(--pf-global--BorderColor--100);
                }

                .pf-c-brand img {
                    padding: 0 0.5rem;
                    height: 42px;
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

    render(): TemplateResult {
        return html` <a href="#/" class="pf-c-page__header-brand-link">
            <div class="pf-c-brand ak-brand">
                <img
                    src=${themeImage(this.brand?.brandingLogo ?? DefaultBrand.brandingLogo)}
                    alt="${msg("authentik Logo")}"
                    loading="lazy"
                />
            </div>
        </a>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar-brand": SidebarBrand;
    }
}
