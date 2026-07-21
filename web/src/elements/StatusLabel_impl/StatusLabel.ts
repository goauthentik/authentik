import { Label, type Status } from "#elements/Label_impl/Label";

import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { html } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

// A translation table, since we use "error" as a danger signal
const negativeStatus: Record<string, Status> = {
    error: "danger",
    warning: "warning",
    info: "info",
    neutral: "neutral",
};

export class StatusLabel extends Label {
    @property({ type: Boolean, reflect: true })
    public good?: boolean = false;

    @property({ attribute: "good-label" })
    public goodLabel = msg("Yes");

    @property({ attribute: "bad-label" })
    public badLabel = msg("No");

    @property({ attribute: "neutral-label" })
    public neutralLabel = msg("-");

    @property({ type: Boolean, reflect: true })
    public compact = false;

    @property()
    public type: "error" | "warning" | "info" | "neutral" = "error";

    public override connectedCallback() {
        super.connectedCallback();
        if (!this.hasAttribute("role")) this.setAttribute("role", "status");
    }

    public override willUpdate() {
        [this.status, this.label] = match(this.good)
            .with(P.nullish, () => ["unknown", this.neutralLabel])
            .with(true, () => ["good", this.goodLabel])
            .with(false, () => [negativeStatus[this.type] ?? "danger", this.badLabel])
            .exhaustive();
    }
}

export type StatusLabelType = "error" | "warning" | "info" | "neutral";

export type StatusLabelProps = Partial<
    Pick<StatusLabel, "good" | "goodLabel" | "badLabel" | "neutralLabel" | "compact" | "type">
>;

export function akStatusLabel(properties: StatusLabelProps = {}) {
    const { good, goodLabel, badLabel, neutralLabel, compact, type } = properties;

    // `.good` is passed as a property to preserve the `undefined` (so "unknown") state
    return html`<ak-status-label
        type=${ifDefined(type)}
        .good=${good}
        good-label=${ifDefined(goodLabel)}
        bad-label=${ifDefined(badLabel)}
        neutral-label=${ifDefined(neutralLabel)}
        ?compact=${compact}
    ></ak-status-label>`;
}
