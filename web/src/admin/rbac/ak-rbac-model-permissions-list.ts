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
    assigned: boolean;
}

const Style = css`
    :host {
        --ak-c-permissions-list--ColumnWidth: repeat(auto-fit, minmax(16em, 1fr));
        --ak-c-permissions-list--ColumnGap: var(--pf-global--spacer--xl);
        --ak-c-permissions-list--RowGap: var(--pf-global--spacer--sm);
        --ak-c-permissions-list--item--InnerGap: var(--pf-global--spacer--sm);
        --ak-c-permissions-list--icon--Gap: var(--pf-global--spacer--xs);
    }

    ul {
        display: grid;
        grid-template-columns: var(--ak-c-permissions-list--ColumnWidth);
        column-gap: var(--ak-c-permissions-list--ColumnGap);
        row-gap: var(--ak-c-permissions-list--RowGap);
        list-style: none;
        padding: 0;
    }

    li {
        word-break: normal;
        flex-wrap: nowrap;
        align-items: flex-start;
        display: flex;
        flex-direction: row;
        gap: var(--ak-c-permissions-list--item--InnerGap);
    }

    li i {
        text-align: center;
        margin-top: 0.33ex;
        width: 1.75ch;
    }

    li pf-tooltip,
    li span {
        flex: 1 1 auto;
    }

    li ak-label {
        flex: 0 1 auto;
    }
`;

@customElement("ak-rbac-model-permissions-list")
export class RbacModelPermissionsList extends AKElement {
    static readonly styles = [Style, PFCard];

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

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-model-permissions-list": RbacModelPermissionsList;
    }
}
