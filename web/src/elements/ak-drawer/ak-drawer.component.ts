import Style from "./ak-drawer.css";

import { AKElement } from "#elements/Base";
import { classList } from "#elements/directives/class-list";

import { html } from "lit";
import { property } from "lit/decorators.js";

import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";

export class Drawer extends AKElement {
    static readonly styles = [PFDrawer, Style];

    @property({ type: Boolean, reflect: true })
    public open = false;

    render() {
        const open = [(this.open && "pf-m-expanded") || "pf-m-collapsed"];

        return html`
            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer ${classList(open)}" id="flow-drawer">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                <slot></slot>
                            </div>
                        </div>
                        <div class="pf-c-drawer__panel pf-m-width-33">
                            <slot name="panel"></slot>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}
