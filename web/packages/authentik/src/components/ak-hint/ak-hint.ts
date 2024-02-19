import { AKElement } from "@goauthentik/app/elements/Base";

import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

const styles = css`
    :host {
        --ak-hint--GridRowGap: var(--pf-global--spacer--md);
        --ak-hint--PaddingTop: var(--pf-global--spacer--md);
        --ak-hint--PaddingRight: var(--pf-global--spacer--lg);
        --ak-hint--PaddingBottom: var(--pf-global--spacer--md);
        --ak-hint--PaddingLeft: var(--pf-global--spacer--lg);
        --ak-hint--BackgroundColor: var(--pf-global--palette--blue-50);
        --ak-hint--BorderColor: var(--pf-global--palette--blue-100);
        --ak-hint--BorderWidth: var(--pf-global--BorderWidth--sm);
        --ak-hint--BoxShadow: var(--pf-global--BoxShadow--sm);
        --ak-hint--Color: var(--pf-global--Color--100);

        /* Hint Title */
        --ak-hint__title--FontSize: var(--pf-global--FontSize--lg);

        /* Hint Body */
        --ak-hint__body--FontSize: var(--pf-global--FontSize--md);

        /* Hint Footer */
        --ak-hint__footer--child--MarginRight: var(--pf-global--spacer--md);

        /* Hint Actions */
        --ak-hint__actions--MarginLeft: var(--pf-global--spacer--2xl);
        --ak-hint__actions--c-dropdown--MarginTop: calc(
            var(--pf-global--spacer--form-element) * -1
        );
    }

    :host([theme="dark"]) {
        --ak-hint--BackgroundColor: var(--ak-dark-background-darker);
        --ak-hint--BorderColor: var(--ak-dark-background-lighter);
        --ak-hint--Color: var(--ak-dark-foreground);
    }

    div#host {
        display: flex;
        flex-direction: column;
        gap: var(--ak-hint--GridRowGap);
        background-color: var(--ak-hint--BackgroundColor);
        color: var(--ak-hint--Color);
        border: var(--ak-hint--BorderWidth) solid var(--ak-hint--BorderColor);
        box-shadow: var(--ak-hint--BoxShadow);
        padding: var(--ak-hint--PaddingTop) var(--ak-hint--PaddingRight)
            var(--ak-hint--PaddingBottom) var(--ak-hint--PaddingLeft);
    }

    ::slotted(ak-hint-title),
    ::slotted(ak-hint-body) {
        display: grid;
        grid-template-columns: 1fr auto;
        grid-row-gap: var(--ak-hint--GridRowGap);
    }
`;

@customElement("ak-hint")
export class AkHint extends AKElement {
    static get styles() {
        return [styles];
    }

    render() {
        return html`<div part="ak-hint" id="host"><slot></slot></div>`;
    }
}

export default AkHint;
