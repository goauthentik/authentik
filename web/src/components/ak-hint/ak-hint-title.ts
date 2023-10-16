import { AKElement } from "@goauthentik/app/elements/Base";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

const style = css`
    #host {
        font-size: var(--ak-hint__title--FontSize);
    }
`;

@customElement("ak-hint-title")
export class AkHintTitle extends AKElement {
    static get styles() {
        return [style];
    }

    render() {
        return html`<div id="host" part="ak-hint-title"><slot></slot></div>`;
    }
}

export default AkHintTitle;
