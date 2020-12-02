import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import PageStyle from "@patternfly/patternfly/components/Page/page.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
import { Config } from "../../api/config";

export const DefaultConfig: Config = {
    branding_logo: " /static/dist/assets/images/logo.svg",
    branding_title: "passbook",

    error_reporting_enabled: false,
    error_reporting_environment: "",
    error_reporting_send_pii: false,
};

@customElement("pb-sidebar-brand")
export class SidebarBrand extends LitElement {
    @property({attribute: false})
    config: Config = DefaultConfig;

    static get styles(): CSSResult[] {
        return [
            GlobalsStyle,
            PageStyle,
            css`
                .pf-c-brand {
                    font-family: "DIN 1451 Std";
                    line-height: 60px;
                    font-size: 3rem;
                    color: var(--pf-c-nav__link--m-current--Color);
                    display: flex;
                    flex-direction: row;
                    justify-content: center;
                    width: 100%;
                    margin: 0 1rem;
                    margin-bottom: 1.5rem;
                }
                .pf-c-brand img {
                    max-height: 60px;
                    margin-right: 8px;
                }
            `,
        ];
    }

    constructor() {
        super();
        Config.get().then((c) => (this.config = c));
    }

    render(): TemplateResult {
        if (!this.config) {
            return html``;
        }
        return html` <a href="#/" class="pf-c-page__header-brand-link">
            <div class="pf-c-brand pb-brand">
                <img src="${this.config.branding_logo}" alt="passbook icon" loading="lazy" />
                ${this.config.branding_title
        ? html`<span>${this.config.branding_title}</span>`
        : ""}
            </div>
        </a>`;
    }
}
