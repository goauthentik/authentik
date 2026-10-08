import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/Label";
import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { AKElement } from "#elements/Base";

import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface PermissionDisplay {
    name: string;
    kind: string | null;
    tag: string | null;
    active: boolean;
}

const Style = css`
    ul {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
        column-gap: 2rem;
        row-gap: 0.5rem;
        list-style: none;
        padding: 0;
    }

    li {
        word-break: normal;
        align-content: flex-start;
        align-items: flex-start;
        display: flex;
        flex-direction: row;
        gap: 0.25rem;
    }

    li i {
        margin-top: 0.33ex;
        display: flex;
        flex-direction: row;
        gap: 0.125rem;
        flex-wrap: nowrap;
        white-space: nowrap;
    }
`;

@customElement("ak-rbac-model-permission-list")
export class ModelPermissionsCard extends AKElement {
    static readonly styles = [PFCard, Style];

    @property({ type: Array })
    items: PermissionDisplay[] = [];

    renderLabel() {}

    render() {
        return html`<ul part="permissions">
            ${this.items.map(
                ({ name, kind, tag }: PermissionDisplay) =>
                    html`<li>
                        ${
                            kind
                                ? html`
                                      <i class="fas fa-check pf-m-success" aria-hidden="true"></i
                                      ><pf-tooltip position="top" content=${kind}
                                          >${name}</pf-tooltip
                                      ><ak-label compact color="info">${tag}</ak-label>
                                  `
                                : html`
                                      <i class="fas fa-times pf-m-danger" aria-hidden="true"></i>
                                      <span>${name}</span>
                                  `
                        }
                    </li>`,
            )}
        </ul>`;
    }
}
