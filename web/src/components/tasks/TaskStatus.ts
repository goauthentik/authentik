import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKElement } from "#elements/Base";
import { akLabel, PFColor } from "#elements/Label";

import { LastTaskStatusEnum, TaskAggregatedStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

type Status = TaskAggregatedStatusEnum | LastTaskStatusEnum;
type StatusRepresentation = [string, PFColor, ...Status[]];

const C = PFColor;
const TA = TaskAggregatedStatusEnum;
const LT = LastTaskStatusEnum;

// prettier-ignore
const statusRepresentation: StatusRepresentation[] = [
    [msg("Waiting for dependencies"), C.Gray, TA.WaitingForDependencies, LT.WaitingForDependencies],
    [msg("Waiting to run"),  C.Gray,   TA.Queued, LT.Queued],
    [msg("Consumed"),        C.Blue,   TA.Consumed, LT.Consumed],
    [msg("Pre-processing"),  C.Blue,   TA.Preprocess, LT.Preprocess],
    [msg("Running"),         C.Blue,   TA.Running, LT.Running],
    [msg("Post-processing"), C.Blue,   TA.Postprocess, LT.Postprocess],
    [msg("Successful"),      C.Green,  TA.Done, LT.Done, TA.Info, LT.Info],
    [msg("Warning"),         C.Orange, TA.Warning, LT.Warning],
    [msg("Error"),           C.Red,    TA.Rejected, LT.Rejected, TA.Error, LT.Error],
];

@customElement("ak-task-status")
export class TaskStatus extends AKElement {
    public static styles: CSSResult[] = [PFButton];

    @property()
    status?: TaskAggregatedStatusEnum | LastTaskStatusEnum;

    rep: StatusRepresentation = [msg("Unset"), C.Gray];

    willUpdate(changed: PropertyValues<this>) {
        if (changed.has("status")) {
            this.rep = statusRepresentation.find((s) => s.slice(2).find((t) => t === this.status)) ?? [
                msg("Unknown"),
                C.Gray,
            ];
        }
    }

    render() {
        return akLabel({ color: this.rep[1] }, this.rep[0]);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-task-status": TaskStatus;
    }
}
