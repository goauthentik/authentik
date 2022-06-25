import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFChip from "@patternfly/patternfly/components/Chip/chip.css";
import PFChipGroup from "@patternfly/patternfly/components/ChipGroup/chip-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Chip } from "./Chip";

@customElement("ak-chip-group")
export class ChipGroup extends LitElement {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFChip,
            PFChipGroup,
            PFButton,
            AKGlobal,
            css`
                ::slotted(*) {
                    margin: 0 2px;
                }
                .pf-c-chip-group {
                    margin-bottom: 8px;
                }
            `,
        ];
    }

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
        return html`<div class="pf-c-chip-group">
            <div class="pf-c-chip-group__main">
                <ul class="pf-c-chip-group__list" role="list">
                    <slot></slot>
                </ul>
            </div>
        </div>`;
    }
}
