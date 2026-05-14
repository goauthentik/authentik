import { AKElement } from "#elements/Base";
import { Chip } from "#elements/chips/Chip";
import { SlottedTemplateResult } from "#elements/types";

import { css, CSSResult, html } from "lit";
import { createRef, ref } from "lit-html/directives/ref.js";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFChip from "@patternfly/patternfly/components/Chip/chip.css";
import PFChipGroup from "@patternfly/patternfly/components/ChipGroup/chip-group.css";

@customElement("ak-chip-group")
export class ChipGroup<T = string | number> extends AKElement {
    public static styles: CSSResult[] = [
        PFChip,
        PFChipGroup,
        PFButton,
        css`
            :host {
                display: block;
            }
            .pf-c-chip-group {
                margin-bottom: 8px;
            }
            .pf-c-chip-group__list {
                gap: var(--pf-global--spacer--xs);
            }
        `,
    ];

    @property({ type: String })
    public name?: string;

    @property({ type: String })
    public placeholder: string | null = null;

    public set value(v: T[]) {
        return;
    }

    public get value(): T[] {
        const values: T[] = [];

        for (const { value } of this.querySelectorAll<Chip>("ak-chip")) {
            if (typeof value === "undefined") {
                continue;
            }

            values.push(value as T);
        }

        return values;
    }

    protected defaultSlotRef = createRef<HTMLSlotElement>();

    public get defaultSlot(): HTMLSlotElement | null {
        return this.defaultSlotRef.value || null;
    }

    public constructor() {
        super();
        this.addEventListener("click", this.interceptClick, {
            capture: true,
        });
    }

    /**
     * Intercept clicks on the chip group, marking the default as prevented
     * if the click did not directly target the chip group itself.
     *
     * This allows the group to have a click listener, while still allowing clicks
     * on the chips themselves.
     */
    protected interceptClick(event: MouseEvent) {
        if (event.target !== this) {
            event.preventDefault();
        }
    }

    protected render(): SlottedTemplateResult {
        return html`<div class="pf-c-chip-group" part="chip-group">
            <div class="pf-c-chip-group__main">
                <ul class="pf-c-chip-group__list">
                    <slot ${ref(this.defaultSlotRef)}>
                        <div class="ak-m-placeholder pf-m-pressable">${this.placeholder}</div>
                    </slot>
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
