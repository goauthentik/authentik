import { LitElement, html, customElement, property } from "lit-element";
// @ts-ignore
import TabsStyle from "@patternfly/patternfly/components/Tabs/tabs.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
import { CURRENT_CLASS } from "../constants";

@customElement("pb-tabs")
export class Tabs extends LitElement {
    @property()
    currentPage?: string;

    static get styles() {
        return [GlobalsStyle, TabsStyle];
    }

    render() {
        let pages = Array.from(this.querySelectorAll("[slot]")!);
        if (!this.currentPage) {
            if (pages.length < 1) {
                return html`<h1>no tabs defined</h1>`;
            }
            this.currentPage = pages[0].attributes.getNamedItem("slot")?.value;
        }
        return html`<div class="pf-c-tabs">
                <ul class="pf-c-tabs__list">
                    ${pages.map((page) => {
                        const slot = page.attributes.getNamedItem("slot")?.value;
                        return html` <li
                            class="pf-c-tabs__item ${slot === this.currentPage
                                ? CURRENT_CLASS
                                : ""}"
                        >
                            <button
                                class="pf-c-tabs__link"
                                @click=${() => {
                                    this.currentPage = slot;
                                }}
                            >
                                <span class="pf-c-tabs__item-text">
                                    ${page.attributes.getNamedItem("tab-title")?.value}
                                </span>
                            </button>
                        </li>`;
                    })}
                </ul>
            </div>
            <slot name="${this.currentPage}"></slot>`;
    }
}
