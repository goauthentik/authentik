import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKElement } from "#elements/Base";
import { akLabel } from "#elements/Label";

import { LastTaskStatusEnum, TaskAggregatedStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

type Status = TaskAggregatedStatusEnum | LastTaskStatusEnum;
type StatusRepresentation = [string, string, ...Status[]];

const TA = TaskAggregatedStatusEnum;
const LT = LastTaskStatusEnum;

// prettier-ignore
const statusRepresentation: StatusRepresentation[] = [
    [msg("Waiting for dependencies"), "gray", TA.WaitingForDependencies, LT.WaitingForDependencies],
    [msg("Waiting to run"),  "gray",   TA.Queued, LT.Queued],
    [msg("Consumed"),        "blue",   TA.Consumed, LT.Consumed],
    [msg("Pre-processing"),  "blue",   TA.Preprocess, LT.Preprocess],
    [msg("Running"),         "blue",   TA.Running, LT.Running],
    [msg("Post-processing"), "blue",   TA.Postprocess, LT.Postprocess],
    [msg("Successful"),      "green",  TA.Done, LT.Done, TA.Info, LT.Info],
    [msg("Warning"),         "orange", TA.Warning, LT.Warning],
    [msg("Error"),           "red",    TA.Rejected, LT.Rejected, TA.Error, LT.Error],
];

/*
 * TaskStatus
 *
 * A specialized wrapper around `<ak-label />` that understands the Task Status indicator as used on
 * the authentik server and presents a chip with a distinct color and unified labeling scheme for
 * different conditions.  Used in a lot of Task Status and Schedule Status tables.
 */

@customElement("ak-task-status")
export class TaskStatus extends AKElement {
    public static styles: CSSResult[] = [PFButton];

    @property()
    status?: TaskAggregatedStatusEnum | LastTaskStatusEnum;

    rep: StatusRepresentation = [msg("Unset"), "red"];

    willUpdate(changed: PropertyValues<this>) {
        if (changed.has("status")) {
            this.rep = statusRepresentation.find((s) =>
                s.slice(2).find((t) => t === this.status),
            ) ?? [msg("Unknown"), "gray"];
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
