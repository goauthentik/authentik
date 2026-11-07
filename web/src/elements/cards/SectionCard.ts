import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { AKElement } from "#elements/Base";

import { SlotController } from "@patternfly/pfe-core/controllers/slot-controller.js";

import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * @element ak-section-card
 *
 * A mostly visual element meant to provide a better visual hierarchy in locations where we have
 * lots of nested information. Meant to make the expansion rows easier to read.
 */

const Styles = css`
    :host {
        display: block;
    }

    * [hidden] {
        display: none;
    }
`;

@customElement("ak-section-card")
export class SectionCard extends AKElement {
    public static styles = [PFCard, Styles];

    protected slots = new SlotController(this, {
        slots: [null, "description"],
    });

    @property({ type: String })
    public label: string = "";

    protected override render() {
        const hideTitle = !this.label || this.label.trim() === "";
        const hideDesc = !this.slots.hasSlotted("description");

        return html`<section class="pf-c-card" aria-labelledby="card-title" part="card">
            <div class="pf-c-card__header" part="card-header" ?hidden=${hideTitle}>
                <h3 class="pf-c-card__title" id="card-title" part="card-title">${this.label}</h3>
            </div>
            <div class="pf-c-card__body" part="card-description" ?hidden=${hideDesc}>
                <slot name="description"></slot>
            </div>
            <div part="card-body">
                <slot></slot>
            </div>
        </section>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-section-card": SectionCard;
    }
}
