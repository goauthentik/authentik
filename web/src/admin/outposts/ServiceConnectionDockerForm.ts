import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CertificateKeyPair,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    DockerServiceConnection,
    OutpostsApi,
} from "@goauthentik/api";

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
                    <span class="pf-c-switch__label">${t`Local`}</span>
                </label>
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
                    ${t`Can be in the format of 'unix://' when connecting to a local docker daemon, using 'ssh://' to connect via SSH, or 'https://:2376' when connecting to a remote system.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`TLS Verification Certificate`}
                name="tlsVerification"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<CertificateKeyPair[]> => {
                        const args: CryptoCertificatekeypairsListRequest = {
                            ordering: "name",
                            hasKey: true,
                            includeDetails: false,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const certificates = await new CryptoApi(
                            DEFAULT_CONFIG,
                        ).cryptoCertificatekeypairsList(args);
                        return certificates.results;
                    }}
                    .renderElement=${(item: CertificateKeyPair): string => {
                        return item.name;
                    }}
                    .value=${(item: CertificateKeyPair | undefined): string | undefined => {
                        return item?.pk;
                    }}
                    .selected=${(item: CertificateKeyPair): boolean => {
                        return this.instance?.tlsVerification === item.pk;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${t`CA which the endpoint's Certificate is verified against. Can be left empty for no validation.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`TLS Authentication Certificate/SSH Keypair`}
                name="tlsAuthentication"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<CertificateKeyPair[]> => {
                        const args: CryptoCertificatekeypairsListRequest = {
                            ordering: "name",
                            hasKey: true,
                            includeDetails: false,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const certificates = await new CryptoApi(
                            DEFAULT_CONFIG,
                        ).cryptoCertificatekeypairsList(args);
                        return certificates.results;
                    }}
                    .renderElement=${(item: CertificateKeyPair): string => {
                        return item.name;
                    }}
                    .value=${(item: CertificateKeyPair | undefined): string | undefined => {
                        return item?.pk;
                    }}
                    .selected=${(item: CertificateKeyPair): boolean => {
                        return this.instance?.tlsAuthentication === item.pk;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${t`Certificate/Key used for authentication. Can be left empty for no authentication.`}
                </p>
                <p class="pf-c-form__helper-text">
                    ${t`When connecting via SSH, this keypair is used for authentication.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
