import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import YAML from "yaml";

import { t } from "@lingui/macro";

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
            return t`Successfully updated integration.`;
        } else {
            return t`Successfully created integration.`;
        }
    }

    send = (data: KubernetesServiceConnection): Promise<KubernetesServiceConnection> => {
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
            <ak-form-element-horizontal label=${t`Kubeconfig`} name="kubeconfig">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(first(this.instance?.kubeconfig, {}))}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Set custom attributes using YAML or JSON.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
