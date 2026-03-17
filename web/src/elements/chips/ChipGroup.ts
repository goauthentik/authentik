import { AKElement } from "#elements/Base";
import { Chip } from "#elements/chips/Chip";

import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFChip from "@patternfly/patternfly/components/Chip/chip.css";
import PFChipGroup from "@patternfly/patternfly/components/ChipGroup/chip-group.css";

@customElement("ak-chip-group")
export class ChipGroup extends AKElement {
    static styles: CSSResult[] = [
        PFChip,
        PFChipGroup,
        PFButton,
        css`
            .pf-c-chip-group {
                margin-bottom: 8px;
            }
            .pf-c-chip-group__list {
                gap: var(--pf-global--spacer--xs);
            }
        `,
    ];

    @property()
    name?: string;

    set value(v: (string | number | undefined)[]) {
        return;
    }

    get value(): (string | number | undefined)[] {
        const values: (string | number | undefined)[] = [];
        this.querySelectorAll<Chip>("ak-chip").forEach((chip) => {
            values.push(chip.value);
        });
        return values;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-chip-group" part="chip-group">
            <div class="pf-c-chip-group__main">
                <ul class="pf-c-chip-group__list">
                    <slot></slot>
                </ul>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-chip-group": ChipGroup;
    }
}
