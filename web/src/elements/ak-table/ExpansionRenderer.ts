import { bound } from "@goauthentik/elements/decorators/bound";

import { LitElement, html, nothing } from "lit";
import { state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

import type { TableRow } from "./types";

type Constructor<T = object> = {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    new (...args: any[]): T;
    prototype: T;
};

export function ExpansionRenderer<T extends Constructor<LitElement>>(superclass: T) {
    const parentStyles = (superclass as unknown as typeof LitElement)?.styles ?? [];

    class ExpansionRenderer extends superclass {
        static get styles() {
            return [parentStyles, PFButton];
        }

        @state()
        expandedRows: number[] = [];

        protected onExpansion(ev: Event, rowidx: number) {
            ev.stopPropagation();
            this.expandedRows = this.expandedRows.includes(rowidx)
                ? this.expandedRows.filter((v) => v !== rowidx)
                : [...this.expandedRows, rowidx];
        }

        @bound
        renderExpansionControl(rowidx: number, expanded: boolean) {
            const expandedClass = { "pf-m-expanded": expanded };
            return html`<td part="expand-cell" class="pf-c-table__toggle" role="cell">
                <button
                    class="pf-c-button pf-m-plain ${classMap(expandedClass)}"
                    @click=${(ev: Event) => this.onExpansion(ev, rowidx)}
                >
                    <div part="expand-icon" class="pf-c-table__toggle-icon">
                        &nbsp;<i class="fas fa-angle-down" aria-hidden="true"></i>&nbsp;
                    </div>
                </button>
            </td>`;
        }

        @bound
        renderExpansion(row: TableRow, expanded: boolean) {
            return row.expansion && expanded
                ? html` <tr
                      part="expansion-row"
                      class="pf-c-table__expandable-row pf-m-expanded"
                      role="row"
                  >
                      <td></td>
                      <td part="expansion-content">${row.expansion()}</td>
                  </tr>`
                : nothing;
        }
    }
    return ExpansionRenderer;
}
