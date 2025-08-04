import "#elements/Spinner";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { OutpostHealth, OutpostsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-outpost-health-simple")
export class OutpostHealthSimpleElement extends AKElement {
    @property()
    public outpostId?: string;

    @state()
    protected outpostHealths: OutpostHealth[] = [];

    @property({ attribute: false })
    public loaded = false;

    @property({ attribute: false })
    public showVersion = true;

    public static override styles: CSSResult[] = [PFBase];

    public constructor() {
        super();
        window.addEventListener(EVENT_REFRESH, () => {
            this.outpostHealths = [];
            this.firstUpdated();
        });
    }

    public override firstUpdated(): void {
        if (!this.outpostId) return;
        new OutpostsApi(DEFAULT_CONFIG)
            .outpostsInstancesHealthList({
                uuid: this.outpostId,
            })
            .then((health) => {
                this.loaded = true;
                this.outpostHealths = health;
            });
    }

    public override render(): TemplateResult {
        if (!this.outpostId || !this.loaded) {
            return html`<ak-spinner></ak-spinner>`;
        }
        if (!this.outpostHealths || this.outpostHealths.length === 0) {
            return html`<ak-label color=${PFColor.Grey}>${msg("Not available")}</ak-label>`;
        }
        const outdatedOutposts = this.outpostHealths.filter((h) => h.versionOutdated);
        if (outdatedOutposts.length > 0) {
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
