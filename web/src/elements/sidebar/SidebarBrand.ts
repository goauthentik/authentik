import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import PageStyle from "@patternfly/patternfly/components/Page/page.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
import { Config } from "../../api/config";

export const DefaultConfig: Config = {
    branding_logo: " /static/dist/assets/icons/icon_left_brand.svg",
    branding_title: "authentik",

    error_reporting_enabled: false,
    error_reporting_environment: "",
    error_reporting_send_pii: false,
};

@customElement("ak-sidebar-brand")
export class SidebarBrand extends LitElement {
    @property({attribute: false})
    config: Config = DefaultConfig;

    static get styles(): CSSResult[] {
        return [
            GlobalsStyle,
            PageStyle,
            css`
                :host {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    height: 82px;
                }
                .pf-c-brand img {
                    width: 100%;
                    padding: 0 .5rem;
                }
            `,
        ];
    }

    firstUpdated() {
        Config.get().then((c) => (this.config = c));
    }

    render(): TemplateResult {
        return html` <a href="#/" class="pf-c-page__header-brand-link">
            <div class="pf-c-brand ak-brand">
                <img src="${this.config.branding_logo}" alt="authentik icon" loading="lazy" />
            </div>
        </a>`;
    }
}
