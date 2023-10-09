import { AKElement } from "@goauthentik/app/elements/Base";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

const style = css`
    ::slotted(*) {
        font-size: var(--ak-hint__title--FontSize);
    }
`;

@customElement("ak-hint-title")
export class AkHintTitle extends AKElement {
    get styles() {
        return [style];
    }

    render() {
        return html`<div><slot></slot></div>`;
    }
}

export default AkHintTitle;
