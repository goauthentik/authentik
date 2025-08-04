import { AKElement } from "#elements/Base";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

const style = css`
    #host {
        font-size: var(--ak-hint__title--FontSize);
    }
`;

@customElement("ak-hint-title")
export class AkHintTitle extends AKElement {
    public static override styles = [style];

    public override render() {
        return html`<div id="host" part="ak-hint-title"><slot></slot></div>`;
    }
}

export default AkHintTitle;

declare global {
    interface HTMLElementTagNameMap {
        "ak-hint-title": AkHintTitle;
    }
}
