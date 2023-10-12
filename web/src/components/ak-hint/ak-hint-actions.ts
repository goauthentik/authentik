import { AKElement } from "@goauthentik/app/elements/Base";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

const style = css`
    div {
        display: inline-grid;
        grid-row: 1;
        grid-column: 2;
        grid-auto-flow: column;
        margin-left: var(--ak-hint__actions--MarginLeft);
        text-align: right;
    }

    ::slotted(ak-hint-body) {
        grid-column: 1;
    }
`;

@customElement("ak-hint-actions")
export class AkHintActions extends AKElement {
    static get styles() {
        return [style];
    }

    render() {
        return html`<div part="ak-hint-actions"><slot></slot></div>`;
    }
}

export default AkHintActions;
