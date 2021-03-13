import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import PageStyle from "@patternfly/patternfly/components/Page/page.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
import { configureSentry } from "../../api/Config";
import { Config } from "../../api";
import { ifDefined } from "lit-html/directives/if-defined";

export const DefaultConfig: Config = {
    brandingLogo: " /static/dist/assets/icons/icon_left_brand.svg",
    brandingTitle: "authentik",

    errorReportingEnabled: false,
    errorReportingEnvironment: "",
    errorReportingSendPii: false,
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
                    height: 42px;
                }
            `,
        ];
    }

    firstUpdated(): void {
        configureSentry().then((c) => {this.config = c;});
    }

    render(): TemplateResult {
        return html` <a href="#/" class="pf-c-page__header-brand-link">
            <div class="pf-c-brand ak-brand">
                <img src="${ifDefined(this.config.brandingLogo)}" alt="authentik icon" loading="lazy" />
            </div>
        </a>`;
    }
}
