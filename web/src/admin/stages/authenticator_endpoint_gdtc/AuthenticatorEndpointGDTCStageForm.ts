import "#elements/CodeMirror";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { AKLabel } from "#components/ak-label";

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
            <ak-form-element-horizontal required name="name">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "name",
                        required: true,
                    },
                    msg("Name"),
                )}
                <input
                    id="name"
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Google Verified Access API")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="credentials">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "credentials",
                                required: true,
                            },
                            msg("Credentials"),
                        )}
                        <ak-codemirror
                            id="credentials"
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
