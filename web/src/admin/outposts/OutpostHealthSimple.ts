import "#elements/Spinner";

import { aki } from "#common/api/client";
import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";
import { PFColor } from "#elements/Label";
import { AKTableRefreshEvent } from "#elements/table/events";
import { SlottedTemplateResult } from "#elements/types";
import { dateProperty } from "#elements/utils/properties";

import { OutpostHealth, OutpostsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-outpost-health-simple")
export class OutpostHealthSimpleElement extends AKElement {
    @property({ type: String, attribute: "outpost-id" })
    public outpostID: string | null = null;

    @state()
    protected outpostHealths: OutpostHealth[] = [];

    /**
     * A timestamp of the last attempt to refresh the outpost health.
     */
    @property(dateProperty)
    public lastRefreshedAt: Date | null = null;

    @listen(AKTableRefreshEvent, { target: window })
    public refresh = (event?: AKTableRefreshEvent) => {
        if (!this.outpostID) return;

        if (event) {
            if (!this.lastRefreshedAt) return;
            if (!event.table.renderRoot.contains(this)) return;
        }

        this.outpostHealths = [];

        return aki(OutpostsApi)
            .outpostsInstancesHealthList({
                uuid: this.outpostID,
            })
            .then((health) => {
                this.lastRefreshedAt = new Date();
                this.outpostHealths = health;
            });
    };

    protected override firstUpdated(): void {
        this.refresh();
    }

    protected override render(): SlottedTemplateResult {
        if (!this.outpostID || !this.lastRefreshedAt) {
            return html`<ak-spinner size="md"></ak-spinner>`;
        }

        if (!this.outpostHealths || this.outpostHealths.length === 0) {
            return html`<ak-label color=${PFColor.Gray}>${msg("Not available")}</ak-label>`;
        }

        const outdatedOutposts = this.outpostHealths.filter((h) => h.versionOutdated);

        if (outdatedOutposts.length) {
            return html`<ak-label color=${PFColor.Red}>
                ${msg(
                    str`${outdatedOutposts[0].version}, should be ${outdatedOutposts[0].versionShould}`,
                )}</ak-label
            >`;
        }

        const lastSeen = this.outpostHealths[0].lastSeen;

        return html`<ak-label color=${PFColor.Green}>
            ${msg(
                str`Last seen: ${formatElapsedTime(lastSeen)} (${lastSeen.toLocaleTimeString()})`,
            )}</ak-label
        >`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-outpost-health-simple": OutpostHealthSimpleElement;
    }
}
