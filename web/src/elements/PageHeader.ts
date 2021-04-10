import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import AKGlobal from "../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { TITLE_SUFFIX } from "../constants";

@customElement("ak-page-header")
export class PageHeader extends LitElement {

    @property()
    icon?: string;

    @property({type: Boolean})
    iconImage = false

    @property()
    set header(value: string) {
        if (value !== "") {
            document.title = `${value} - ${TITLE_SUFFIX}`;
        } else {
            document.title = TITLE_SUFFIX;
        }
        this._header = value;
    }

    get header(): string {
        return this._header;
    }

    @property()
    description?: string;

    _header = "";

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFContent, AKGlobal];
    }

    renderIcon(): TemplateResult {
        if (this.icon) {
            if (this.iconImage) {
                return html`<img class="pf-icon" src="${this.icon}" />&nbsp;`;
            }
            return html`<i class=${this.icon}></i>&nbsp;`;
        }
        return html``;
    }

    render(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
            <div class="pf-c-content">
                <h1>
                    ${this.renderIcon()}
                    ${this.header}
                </h1>
                ${this.description ?
                    html`<p>${this.description}</p>`: html``}
            </div>
        </section>`;
    }

}
