import "#components/ak-text-input";
import "#elements/CodeMirror";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AuthenticatorEndpointGDTCStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-stage-authenticator-endpoint-gdtc-form")
export class AuthenticatorEndpointGDTCStageForm extends BaseStageForm<AuthenticatorEndpointGDTCStage> {
    protected endpoints = {
        load: (stageUuid: string) =>
            aki(StagesApi).stagesAuthenticatorEndpointGdtcRetrieve({ stageUuid }),
        create: (authenticatorEndpointGDTCStageRequest: AuthenticatorEndpointGDTCStage) =>
            aki(StagesApi).stagesAuthenticatorEndpointGdtcCreate({
                authenticatorEndpointGDTCStageRequest,
            }),
        update: (
            stageUuid: string,
            patchedAuthenticatorEndpointGDTCStageRequest: AuthenticatorEndpointGDTCStage,
        ) =>
            aki(StagesApi).stagesAuthenticatorEndpointGdtcPartialUpdate({
                stageUuid,
                patchedAuthenticatorEndpointGDTCStageRequest,
            }),
    };

    static styles = [...super.styles, PFBanner];

    protected override renderForm(): TemplateResult {
        return html`<div class="pf-c-banner pf-m-info">
                ${msg("Endpoint Google Chrome Device Trust is in preview.")}
                <a href="mailto:hello+feature/gdtc@goauthentik.io">${msg("Send us feedback!")}</a>
            </div>
            <span>
                ${msg(
                    "Stage used to verify users' browsers using Google Chrome Device Trust. This stage can be used in authentication/authorization flows.",
                )}
            </span>
            <ak-text-input
                label=${msg("Stage Name", {
                    id: "stage.name.label",
                })}
                required
                name="name"
                value=${this.instance?.name || ""}
                placeholder=${msg("Type a name for this stage...", {
                    id: "stage.name.placeholder",
                })}
                ?autofocus=${!this.instance}
            ></ak-text-input>
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
