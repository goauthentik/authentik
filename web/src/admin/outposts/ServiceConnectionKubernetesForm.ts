import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { KubernetesServiceConnection, OutpostsApi } from "@goauthentik/api";

@customElement("ak-service-connection-kubernetes-form")
export class ServiceConnectionKubernetesForm extends ModelForm<
    KubernetesServiceConnection,
    string
> {
    loadInstance(pk: string): Promise<KubernetesServiceConnection> {
        return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesRetrieve({
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

    async send(data: KubernetesServiceConnection): Promise<KubernetesServiceConnection> {
        if (this.instance) {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesUpdate({
                uuid: this.instance.pk || "",
                kubernetesServiceConnectionRequest: data,
            });
        } else {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesCreate({
                kubernetesServiceConnectionRequest: data,
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
            <ak-form-element-horizontal label=${msg("Kubeconfig")} name="kubeconfig">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(first(this.instance?.kubeconfig, {}))}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="verifySsl">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.verifySsl, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label"
                        >${msg("Verify Kubernetes API SSL Certificate")}</span
                    >
                </label>
            </ak-form-element-horizontal>`;
    }
}
