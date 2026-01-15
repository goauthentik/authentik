import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { KubernetesServiceConnection, OutpostsApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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
        return this.instance
            ? msg("Successfully updated integration.")
            : msg("Successfully created integration.");
    }

    async send(data: KubernetesServiceConnection): Promise<KubernetesServiceConnection> {
        if (this.instance) {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesUpdate({
                uuid: this.instance.pk || "",
                kubernetesServiceConnectionRequest: data,
            });
        }
        return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesCreate({
            kubernetesServiceConnectionRequest: data,
        });
    }

    renderForm(): TemplateResult {
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
            <ak-form-element-horizontal label=${msg("Kubeconfig")} name="kubeconfig">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(this.instance?.kubeconfig ?? {})}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="verifySsl"
                label=${msg("Verify Kubernetes API SSL Certificate")}
                ?checked=${this.instance?.verifySsl ?? true}
            >
            </ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-service-connection-kubernetes-form": ServiceConnectionKubernetesForm;
    }
}
