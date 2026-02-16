import { AKElement } from "#elements/Base";

import Styles from "#components/ak-status-label.css";

import { P4Disposition } from "#styles/patternfly/constants";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFLabel from "@patternfly/patternfly/components/Label/label.css";

const statusToDetails = new Map<P4Disposition, [string, string]>([
    [P4Disposition.Error, ["pf-m-red", "fa-times"]],
    [P4Disposition.Warning, ["pf-m-orange", "fa-exclamation-triangle"]],
    [P4Disposition.Info, ["pf-m-gray", "fa-info-circle"]],
    [P4Disposition.Neutral, ["pf-m-gray", "fa-times"]],
]);

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
 * - type="neutral" A grey ✖
 *
 * By default, the messages for "good" and "other" are "Yes" and "No" respectively, but these can be
 * customized with the attributes `good-label` and `bad-label`.
 */

@customElement("ak-status-label")
export class AkStatusLabel extends AKElement {
    static styles = [PFLabel, Styles];

    @property({ type: Boolean })
    good = false;

    @property({ type: String, attribute: "good-label" })
    goodLabel = msg("Yes");

    @property({ type: String, attribute: "bad-label" })
    badLabel = msg("No");

    @property({ type: Boolean })
    compact = false;

    @property({ type: String })
    type: P4Disposition = P4Disposition.Error;

    render() {
        const details = statusToDetails.get(this.type);

        if (!details) {
            throw new TypeError(`Bad status type [${this.type}] passed to ak-status-label`);
        }

        const [label, color, icon] = this.good
            ? [this.goodLabel, "pf-m-green", "fa-check"]
            : [this.badLabel, ...details];

        const classes = {
            "pf-c-label": true,
            [color]: true,
            "pf-m-compact": this.compact,
        };

        return html`<span class="${classMap(classes)}" aria-label=${label} role="status">
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
