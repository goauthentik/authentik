import { AKElement } from "@goauthentik/app/elements/Base";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

const style = css`
    div {
        grid-column: 1 / -1;
        font-size: var(--ak-hint__body--FontSize);
    }
`;

@customElement("ak-hint-body")
export class AkHintBody extends AKElement {
    get styles() {
        return [style];
    }

    render() {
        return html`<div><slot></slot></div>`;
    }
}

export default AkHintBody;
