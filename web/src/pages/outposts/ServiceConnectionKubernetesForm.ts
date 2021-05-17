import { KubernetesServiceConnection, OutpostsApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import YAML from "yaml";
import { first } from "../../utils";
import { ModelForm } from "../../elements/forms/ModelForm";

@customElement("ak-service-connection-kubernetes-form")
export class ServiceConnectionKubernetesForm extends ModelForm<KubernetesServiceConnection, string> {

    loadInstance(pk: string): Promise<KubernetesServiceConnection> {
        return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesRetrieve({
            uuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated service-connection.`;
        } else {
            return t`Successfully created service-connection.`;
        }
    }

    send = (data: KubernetesServiceConnection): Promise<KubernetesServiceConnection> => {
        if (this.instance) {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesUpdate({
                uuid: this.instance.pk || "",
                kubernetesServiceConnectionRequest: data
            });
        } else {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesCreate({
                kubernetesServiceConnectionRequest: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.instance?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="local">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.local, false)}>
                    <label class="pf-c-check__label">
                        ${t`Local`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${t`If enabled, use the local connection. Required Docker socket/Kubernetes Integration.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Kubeconfig`}
                name="kubeconfig">
                <ak-codemirror mode="yaml" value="${YAML.stringify(first(this.instance?.kubeconfig, {}))}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${t`Set custom attributes using YAML or JSON.`}</p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
