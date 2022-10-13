import "@goauthentik/elements/EmptyState";
import "@goauthentik/flow/FormStatic";
import { AccessDeniedStage } from "@goauthentik/flow/stages/access_denied/AccessDeniedStage";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-flow-provider-oauth2-code-finish")
export class DeviceCodeFinish extends AccessDeniedStage {
    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <div class="pf-c-form__group">
                        <p class="big-icon">
                            <i class="pf-icon pf-icon-ok"></i>
                        </p>
                        <h3 class="pf-c-title pf-m-3xl reason">
                            ${t`You've successfully authenticated your device.`}
                        </h3>
                        <hr />
                        <p>${t`You can close this tab now.`}</p>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
