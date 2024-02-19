import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/Spinner";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OutpostHealth, OutpostsApi } from "@goauthentik/api";

@customElement("ak-outpost-health-simple")
export class OutpostHealthSimpleElement extends AKElement {
    @property()
    outpostId?: string;

    @property({ attribute: false })
    outpostHealth?: OutpostHealth;

    @property({ attribute: false })
    loaded = false;

    @property({ attribute: false })
    showVersion = true;

    static get styles(): CSSResult[] {
        return [PFBase];
    }

    constructor() {
        super();
        window.addEventListener(EVENT_REFRESH, () => {
            this.outpostHealth = undefined;
            this.firstUpdated();
        });
    }

    firstUpdated(): void {
        if (!this.outpostId) return;
        new OutpostsApi(DEFAULT_CONFIG)
            .outpostsInstancesHealthList({
                uuid: this.outpostId,
            })
            .then((health) => {
                this.loaded = true;
                if (health.length >= 1) {
                    this.outpostHealth = health[0];
                }
            });
    }

    render(): TemplateResult {
        if (!this.outpostId || !this.loaded) {
            return html`<ak-spinner></ak-spinner>`;
        }
        if (!this.outpostHealth) {
            return html`<ak-label color=${PFColor.Grey}>${msg("Not available")}</ak-label>`;
        }
        return html`<ak-label color=${PFColor.Green}>
            ${msg(str`Last seen: ${this.outpostHealth.lastSeen?.toLocaleTimeString()}`)}</ak-label
        >`;
    }
}
