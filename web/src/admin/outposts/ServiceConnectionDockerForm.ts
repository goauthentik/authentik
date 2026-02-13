import "#admin/common/ak-crypto-certificate-search";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { DockerServiceConnection, OutpostsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-service-connection-docker-form")
export class ServiceConnectionDockerForm extends ModelForm<DockerServiceConnection, string> {
    loadInstance(pk: string): Promise<DockerServiceConnection> {
        return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsDockerRetrieve({
            uuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated integration.")
            : msg("Successfully created integration.");
    }

    async send(data: DockerServiceConnection): Promise<DockerServiceConnection> {
        if (this.instance) {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsDockerUpdate({
                uuid: this.instance.pk || "",
                dockerServiceConnectionRequest: data,
            });
        }
        return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsDockerCreate({
            dockerServiceConnectionRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>

            <ak-switch-input
                name="local"
                label=${msg("Local connection")}
                ?checked=${this.instance?.local ?? false}
                help=${msg("Requires Docker socket/Kubernetes Integration.")}
            >
            </ak-switch-input>

            <ak-form-element-horizontal label=${msg("Docker URL")} required name="url">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.url)}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    inputmode="url"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        html`Can be in the format of <code>unix://</code> when connecting to a local
                            docker daemon, using <code>ssh://</code> to connect via SSH, or
                            <code>https://:2376</code> when connecting to a remote system.`,
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("TLS Verification Certificate")}
                name="tlsVerification"
            >
                <ak-crypto-certificate-search
                    .certificate=${this.instance?.tlsVerification}
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
                    .certificate=${this.instance?.tlsAuthentication}
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-service-connection-docker-form": ServiceConnectionDockerForm;
    }
}
