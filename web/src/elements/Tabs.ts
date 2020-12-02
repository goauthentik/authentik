import { LitElement, html, customElement, property, CSSResult, TemplateResult } from "lit-element";
import { ifDefined } from "lit-html/directives/if-defined";
// @ts-ignore
import TabsStyle from "@patternfly/patternfly/components/Tabs/tabs.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
import { CURRENT_CLASS } from "../constants";

@customElement("pb-tabs")
export class Tabs extends LitElement {
    @property()
    currentPage?: string;

    static get styles(): CSSResult[] {
        return [GlobalsStyle, TabsStyle];
    }

    renderTab(page: Element): TemplateResult {
        const slot = page.attributes.getNamedItem("slot")?.value;
        return html` <li class="pf-c-tabs__item ${slot === this.currentPage ? CURRENT_CLASS : ""}">
            <button class="pf-c-tabs__link" @click=${() => { this.currentPage = slot; }}>
                <span class="pf-c-tabs__item-text">
                    ${page.attributes.getNamedItem("tab-title")?.value}
                </span>
            </button>
        </li>`;
    }

    render(): TemplateResult {
        const pages = Array.from(this.querySelectorAll("[slot]"));
        if (!this.currentPage) {
            if (pages.length < 1) {
                return html`<h1>no tabs defined</h1>`;
            }
            this.currentPage = pages[0].attributes.getNamedItem("slot")?.value;
        }
        return html`<div class="pf-c-tabs">
                <ul class="pf-c-tabs__list">
                    ${pages.map((page) => this.renderTab(page))}
                </ul>
            </div>
            <slot name="${ifDefined(this.currentPage)}"></slot>`;
    }
}
