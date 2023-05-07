import "@goauthentik/elements/EmptyState";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { OAuthDeviceCodeFinishChallenge } from "@goauthentik/api";

@customElement("ak-flow-provider-oauth2-code-finish")
export class DeviceCodeFinish extends BaseStage<
    OAuthDeviceCodeFinishChallenge,
    OAuthDeviceCodeFinishChallenge
> {
    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`<ak-empty-state icon="fas fa-check" header=${t`You may close this page now.`}>
            <span slot="body"> ${t`You've successfully authenticated your device.`} </span>
        </ak-empty-state>`;
    }
}
