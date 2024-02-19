import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export enum Level {
    Warning = "pf-m-warning",
    Info = "pf-m-info",
    Success = "pf-m-success",
    Danger = "pf-m-danger",
}

@customElement("ak-alert")
export class Alert extends AKElement {
    @property({ type: Boolean })
    inline = false;

    @property()
    level: Level = Level.Warning;

    static get styles(): CSSResult[] {
        return [PFBase, PFAlert];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-alert ${this.inline ? "pf-m-inline" : ""} ${this.level}">
            <div class="pf-c-alert__icon">
                <i class="fas fa-exclamation-circle"></i>
            </div>
            <h4 class="pf-c-alert__title">
                <slot></slot>
            </h4>
        </div>`;
    }
}
