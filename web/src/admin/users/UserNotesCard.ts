import "#elements/ak-mdx/ak-mdx";

import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";

@customElement("ak-user-notes-card")
export class UserNotesCard extends AKElement {
    @property({ attribute: false })
    public notes?: unknown;

    static styles: CSSResult[] = [
        PFCard,
        PFContent,
        css`
            .ak-user-notes-empty {
                color: var(--pf-global--Color--200);
                margin: 0;
            }
        `,
    ];

    protected override render() {
        const notes = typeof this.notes === "string" ? this.notes.trim() : "";

        return html`
            <div class="pf-c-card__title">${msg("Notes")}</div>
            <div class="pf-c-card__body">
                ${notes
                    ? html`<ak-mdx .content=${notes}></ak-mdx>`
                    : html`<p class="ak-user-notes-empty">${msg("No notes.")}</p>`}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-notes-card": UserNotesCard;
    }
}
