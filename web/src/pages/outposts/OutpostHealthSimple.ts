import { t } from "@lingui/macro";
import { CSSResult, html, LitElement, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators";
import { OutpostHealth, OutpostsApi } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "../../api/Config";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import "../../elements/Spinner";
import AKGlobal from "../../authentik.css";
import { PFColor } from "../../elements/Label";
import { EVENT_REFRESH } from "../../constants";

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
            return html`<ak-label color=${PFColor.Grey} text=${t`Not available`}></ak-label>`;
        }
        return html` <ak-label
            color=${PFColor.Green}
            text=${t`Last seen: ${this.outpostHealth.lastSeen?.toLocaleTimeString()}`}
        ></ak-label>`;
    }
}
