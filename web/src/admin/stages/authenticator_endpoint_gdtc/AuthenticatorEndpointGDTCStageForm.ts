import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { AuthenticatorEndpointGDTCStage, StagesApi } from "@goauthentik/api";

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
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEndpointGdtcCreate({
                authenticatorEndpointGDTCStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Stage used to configure a duo-based authenticator. This stage should be used for configuration flows.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Google Verified Access API")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Credentials")}
                        ?required=${true}
                        name="credentials"
                    >
                        <ak-codemirror
                            mode=${CodeMirrorMode.JavaScript}
                            .value="${first(this.instance?.credentials, {})}"
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
