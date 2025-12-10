import "#elements/CodeMirror";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AuthenticatorEndpointGDTCStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-stage-authenticator-endpoint-gdtc-form")
export class AuthenticatorEndpointGDTCStageForm extends BaseStageForm<AuthenticatorEndpointGDTCStage> {
    loadInstance(pk: string): Promise<AuthenticatorEndpointGDTCStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEndpointGdtcRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AuthenticatorEndpointGDTCStage): Promise<AuthenticatorEndpointGDTCStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEndpointGdtcPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedAuthenticatorEndpointGDTCStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEndpointGdtcCreate({
            authenticatorEndpointGDTCStageRequest: data,
        });
    }

    static styles = [...super.styles, PFBanner];

    renderForm(): TemplateResult {
        return html`<div class="pf-c-banner pf-m-info">
                ${msg("Endpoint Google Chrome Device Trust is in preview.")}
                <a href="mailto:hello+feature/gdtc@goauthentik.io">${msg("Send us feedback!")}</a>
            </div>
            <span>
                ${msg(
                    "Stage used to verify users' browsers using Google Chrome Device Trust. This stage can be used in authentication/authorization flows.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Google Verified Access API")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Credentials")}
                        required
                        name="credentials"
                    >
                        <ak-codemirror
                            mode="javascript"
                            .value="${this.instance?.credentials ?? {}}"
                        ></ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Google Cloud credentials file.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-endpoint-gdtc-form": AuthenticatorEndpointGDTCStageForm;
    }
}
