import { CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";

import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFChip from "@patternfly/patternfly/components/Chip/chip.css";
import PFChipGroup from "@patternfly/patternfly/components/ChipGroup/chip-group.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../../authentik.css";
import { Chip } from "./Chip";

@customElement("ak-chip-group")
export class ChipGroup extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFChip, PFChipGroup, PFButton, AKGlobal];
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
