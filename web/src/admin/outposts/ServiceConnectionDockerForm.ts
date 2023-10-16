import "@goauthentik/admin/common/ak-crypto-certificate-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { DockerServiceConnection, OutpostsApi } from "@goauthentik/api";

@customElement("ak-service-connection-docker-form")
export class ServiceConnectionDockerForm extends ModelForm<DockerServiceConnection, string> {
    loadInstance(pk: string): Promise<DockerServiceConnection> {
        return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsDockerRetrieve({
            uuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated integration.");
        } else {
            return msg("Successfully created integration.");
        }
    }

    async send(data: DockerServiceConnection): Promise<DockerServiceConnection> {
        if (this.instance) {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsDockerUpdate({
                uuid: this.instance.pk || "",
                dockerServiceConnectionRequest: data,
            });
        } else {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsDockerCreate({
                dockerServiceConnectionRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="local">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.local, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Local")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "If enabled, use the local connection. Required Docker socket/Kubernetes Integration.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Docker URL")} ?required=${true} name="url">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.url)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Can be in the format of 'unix://' when connecting to a local docker daemon, using 'ssh://' to connect via SSH, or 'https://:2376' when connecting to a remote system.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("TLS Verification Certificate")}
                name="tlsVerification"
            >
                <ak-crypto-certificate-search
                    certificate=${this.instance?.tlsVerification}
                ></ak-crypto-certificate-search>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "CA which the endpoint's Certificate is verified against. Can be left empty for no validation.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("TLS Authentication Certificate/SSH Keypair")}
                name="tlsAuthentication"
            >
                <ak-crypto-certificate-search
                    certificate=${this.instance?.tlsAuthentication}
                ></ak-crypto-certificate-search>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Certificate/Key used for authentication. Can be left empty for no authentication.",
                    )}
                </p>
                <p class="pf-c-form__helper-text">
                    ${msg("When connecting via SSH, this keypair is used for authentication.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}
