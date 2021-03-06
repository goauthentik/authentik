import { LitElement, html, customElement, property, CSSResult, TemplateResult, css } from "lit-element";
import { ifDefined } from "lit-html/directives/if-defined";
// @ts-ignore
import TabsStyle from "@patternfly/patternfly/components/Tabs/tabs.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
// @ts-ignore
import AKGlobal from "../authentik.css";
import { CURRENT_CLASS } from "../constants";
import { gettext } from "django";

@customElement("ak-tabs")
export class Tabs extends LitElement {
    @property()
    currentPage?: string;

    @property({type: Boolean})
    vertical = false;

    static get styles(): CSSResult[] {
        return [GlobalsStyle, TabsStyle, AKGlobal, css`
            ::slotted(*) {
                height: 100%;
                flex-grow: 2;
            }
            :host([vertical]) {
                display: flex;
            }
            :host([vertical]) .pf-c-tabs__list {
                height: 100%;
            }
        `];
    }

    renderTab(page: Element): TemplateResult {
        const slot = page.attributes.getNamedItem("slot")?.value;
        return html` <li class="pf-c-tabs__item ${slot === this.currentPage ? CURRENT_CLASS : ""}">
            <button class="pf-c-tabs__link" @click=${() => { this.currentPage = slot; }}>
                <span class="pf-c-tabs__item-text">
                    ${page.getAttribute("data-tab-title")}
                </span>
            </button>
        </li>`;
    }

    render(): TemplateResult {
        const pages = Array.from(this.querySelectorAll("[slot^='page-']"));
        if (!this.currentPage) {
            if (pages.length < 1) {
                return html`<h1>${gettext("no tabs defined")}</h1>`;
            }
            this.currentPage = pages[0].attributes.getNamedItem("slot")?.value;
        }
        return html`<div class="pf-c-tabs ${this.vertical ? "pf-m-vertical pf-m-box" : ""}">
                <ul class="pf-c-tabs__list">
                    ${pages.map((page) => this.renderTab(page))}
                </ul>
            </div>
            <slot name="${ifDefined(this.currentPage)}"></slot>`;
    }
}
