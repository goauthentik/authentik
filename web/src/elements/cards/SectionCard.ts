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

@customElement("ak-section-card")
export class SectionCard extends AKElement {
    public static styles = [
        PFCard,
        css`
            :host {
                display: block;
            }
        `,
    ];

    protected slots = new SlotController(this, {
        slots: [null, "description"],
    });

    @property({ type: String })
    public label: string | null = null;

    protected override render() {
        return html`<section class="pf-c-card" aria-labelledby="card-title" part="card">
            <div class="pf-c-card__header" part="card-header">
                <h3 class="pf-c-card__title" id="card-title" part="card-title">${this.label}</h3>
            </div>
            <div
                class="pf-c-card__body"
                part="card-description"
                ?hidden=${!this.slots.hasSlotted("description")}
            >
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
