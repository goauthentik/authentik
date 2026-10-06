import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { AKElement } from "#elements/Base";

import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

const Style = css`
    ul {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
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
    }
`;

@customElement("ak-model-permissions-card")
export class ModelPermissionsCard extends AKElement {
    static readonly styles = [PFCard, Style];

    @property({ type: Array })
    items: { name: string; kind: string | null }[] = [];

    render() {
        return html`<ul part="permissions">
            ${map(
                this.items,
                ({ name, kind }) =>
                    html`<li>
                        ${
                            kind
                                ? html`<i class="fas fa-check pf-m-success" aria-hidden="true"></i
                                      ><pf-tooltip position="top" content=${kind}
                                          >${name}</pf-tooltip
                                      >`
                                : html`<i class="fas fa-times pf-m-danger" aria-hidden="true"></i
                                      ><span>${name}</span>`
                        }
                    </li>`,
            )}
        </ul>`;
    }
}
