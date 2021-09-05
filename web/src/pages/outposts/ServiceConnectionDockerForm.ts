import { CryptoApi, DockerServiceConnection, OutpostsApi } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import { first } from "../../utils";
import { ModelForm } from "../../elements/forms/ModelForm";

@customElement("ak-service-connection-docker-form")
export class ServiceConnectionDockerForm extends ModelForm<DockerServiceConnection, string> {
    loadInstance(pk: string): Promise<DockerServiceConnection> {
        return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsDockerRetrieve({
            uuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated integration.`;
        } else {
            return t`Successfully created integration.`;
        }
    }

    send = (data: DockerServiceConnection): Promise<DockerServiceConnection> => {
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
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="local">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.local, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Local`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`If enabled, use the local connection. Required Docker socket/Kubernetes Integration.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Docker URL`} ?required=${true} name="url">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.url)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Can be in the format of 'unix://' when connecting to a local docker daemon, or 'https://:2376' when connecting to a remote system.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`TLS Verification Certificate`}
                name="tlsVerification"
            >
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.tlsVerification === undefined}>
                        ---------
                    </option>
                    ${until(
                        new CryptoApi(DEFAULT_CONFIG)
                            .cryptoCertificatekeypairsList({
                                ordering: "pk",
                            })
                            .then((certs) => {
                                return certs.results.map((cert) => {
                                    return html`<option
                                        value=${ifDefined(cert.pk)}
                                        ?selected=${this.instance?.tlsVerification === cert.pk}
                                    >
                                        ${cert.name}
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`CA which the endpoint's Certificate is verified against. Can be left empty for no validation.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`TLS Authentication Certificate`}
                name="tlsAuthentication"
            >
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.tlsAuthentication === undefined}>
                        ---------
                    </option>
                    ${until(
                        new CryptoApi(DEFAULT_CONFIG)
                            .cryptoCertificatekeypairsList({
                                ordering: "pk",
                            })
                            .then((certs) => {
                                return certs.results.map((cert) => {
                                    return html`<option
                                        value=${ifDefined(cert.pk)}
                                        ?selected=${this.instance?.tlsAuthentication === cert.pk}
                                    >
                                        ${cert.name}
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Certificate/Key used for authentication. Can be left empty for no authentication.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
