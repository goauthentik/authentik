import "#elements/EmptyState";
import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { OAuthDeviceCodeFinishChallenge } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-flow-provider-oauth2-code-finish")
export class DeviceCodeFinish extends BaseStage<
    OAuthDeviceCodeFinishChallenge,
    OAuthDeviceCodeFinishChallenge
> {
    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <ak-empty-state icon="fas fa-check">
                <span>${msg("You may close this page now.")}</span>
                <span slot="body"> ${msg("You've successfully authenticated your device.")}</span>
            </ak-empty-state>
        </ak-flow-card>`;
    }
}

export default DeviceCodeFinish;

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-provider-oauth2-code-finish": DeviceCodeFinish;
    }
}
