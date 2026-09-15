import "#components/ak-secret-search-input";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-switch-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { ifPresent } from "#elements/utils/attributes";

import { KubernetesServiceConnection, OutpostsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-service-connection-kubernetes-form")
export class ServiceConnectionKubernetesForm extends ModelForm<
    KubernetesServiceConnection,
    string
> {
    protected endpoints = {
        load: (uuid: string) =>
            aki(OutpostsApi).outpostsServiceConnectionsKubernetesRetrieve({
                uuid,
            }),
        create: (kubernetesServiceConnectionRequest: KubernetesServiceConnection) =>
            aki(OutpostsApi).outpostsServiceConnectionsKubernetesCreate({
                kubernetesServiceConnectionRequest,
            }),
        update: (uuid: string, kubernetesServiceConnectionRequest: KubernetesServiceConnection) =>
            aki(OutpostsApi).outpostsServiceConnectionsKubernetesUpdate({
                uuid,
                kubernetesServiceConnectionRequest,
            }),
    };

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated integration.")
            : msg("Successfully created integration.");
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
            <ak-secret-search-input
                name="secret"
                label=${msg("Kubeconfig", { id: "outpost.kubeconfig.label" })}
                value=${ifPresent(this.instance?.secret)}
                blankable
                help=${msg(
                    "Select a secret containing the kubeconfig as YAML or JSON. Leave empty for a local connection.",
                    { id: "outpost.kubeconfig.description" },
                )}
            ></ak-secret-search-input>
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
