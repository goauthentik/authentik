import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { EVENT_REFRESH } from "@goauthentik/web/constants";
import { PFColor } from "@goauthentik/web/elements/Label";
import "@goauthentik/web/elements/Spinner";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { OutpostHealth, OutpostsApi } from "@goauthentik/api";

@customElement("ak-outpost-health-simple")
export class OutpostHealthSimpleElement extends LitElement {
    @property()
    outpostId?: string;

    @property({ attribute: false })
    outpostHealth?: OutpostHealth;

    @property({ attribute: false })
    loaded = false;

    @property({ attribute: false })
    showVersion = true;

    static get styles(): CSSResult[] {
        return [PFBase, AKGlobal];
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
            return html`<ak-label color=${PFColor.Grey}>${t`Not available`}</ak-label>`;
        }
        return html`<ak-label color=${PFColor.Green}>
            ${t`Last seen: ${this.outpostHealth.lastSeen?.toLocaleTimeString()}`}</ak-label
        >`;
    }
}
