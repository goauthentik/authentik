import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFLabel from "@patternfly/patternfly/components/Label/label.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

// The 'const ... as const' construction will throw a compilation error if the const variable is
// only ever used to generate the type information, so the `_` (ignore unused variable) prefix must
// be used here.
const _statusNames = ["error", "warning", "info"] as const;
type StatusName = (typeof _statusNames)[number];

const statusToDetails = new Map<StatusName, [string, string]>([
    ["error", ["pf-m-red", "fa-times"]],
    ["warning", ["pf-m-orange", "fa-exclamation-triangle"]],
    ["info", ["pf-m-gray", "fa-info-circle"]],
]);

const styles = css`
    :host {
        --pf-c-label--m-gray--BackgroundColor: var(--pf-global--palette--black-100);
        --pf-c-label--m-gray__icon--Color: var(--pf-global--primary-color--100);
        --pf-c-label--m-gray__content--Color: var(--pf-global--info-color--200);
        --pf-c-label--m-gray__content--before--BorderColor: var(--pf-global--palette--black-400);
        --pf-c-label--m-gray__content--link--hover--before--BorderColor: var(
            --pf-global--primary-color--100
        );
        --pf-c-label--m-gray__content--link--focus--before--BorderColor: var(
            --pf-global--primary-color--100
        );
    }

    .pf-c-label.pf-m-gray {
        --pf-c-label--BackgroundColor: var(--pf-c-label--m-gray--BackgroundColor);
        --pf-c-label__icon--Color: var(--pf-c-label--m-gray__icon--Color);
        --pf-c-label__content--Color: var(--pf-c-label--m-gray__content--Color);
        --pf-c-label__content--before--BorderColor: var(
            --pf-c-label--m-gray__content--before--BorderColor
        );
        --pf-c-label__content--link--hover--before--BorderColor: var(
            --pf-c-label--m-gray__content--link--hover--before--BorderColor
        );
        --pf-c-label__content--link--focus--before--BorderColor: var(
            --pf-c-label--m-gray__content--link--focus--before--BorderColor
        );
    }
`;

/**
 * A boolean status indicator
 *
 * Based on the Patternfly "label" pattern, this component exists to display "Yes" or "No", but this
 * is configurable.
 *
 * When the boolean attribute `good` is present, the background will be green and the icon will be a
 * ✓. If the `good` attribute is not present, the background will be a warning color and an
 * alternative symbol. Which color and symbol depends on the `type` of the negative status we want
 * to show:
 *
 * - type="error" (default): A Red ✖
 * - type="warning" An orange ⚠
 * - type="info" A grey ⓘ
 *
 * By default, the messages for "good" and "other" are "Yes" and "No" respectively, but these can be
 * customized with the attributes `good-label` and `bad-label`.
 */

@customElement("ak-status-label")
export class AkStatusLabel extends AKElement {
    static get styles() {
        return [PFBase, PFLabel, styles];
    }

    @property({ type: Boolean })
    good = false;

    @property({ type: String, attribute: "good-label" })
    goodLabel = msg("Yes");

    @property({ type: String, attribute: "bad-label" })
    badLabel = msg("No");

    @property({ type: Boolean })
    compact = false;

    @property({ type: String })
    type: StatusName = "error";

    render() {
        const details = statusToDetails.get(this.type);
        if (!details) {
            throw new Error(`Bad status type [${this.type}] passed to ak-status-label`);
        }

        const [label, color, icon] = this.good
            ? [this.goodLabel, "pf-m-green", "fa-check"]
            : [this.badLabel, ...details];

        const classes = {
            "pf-c-label": true,
            [color]: true,
            "pf-m-compact": this.compact,
        };

        return html`<span class="${classMap(classes)}">
            <span class="pf-c-label__content">
                <span class="pf-c-label__icon">
                    <i class="fas fa-fw ${icon}" aria-hidden="true"></i> </span
                >${label}
            </span>
        </span>`;
    }
}

export default AkStatusLabel;

declare global {
    interface HTMLElementTagNameMap {
        "ak-status-label": AkStatusLabel;
    }
}
