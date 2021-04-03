import { KubernetesServiceConnection, OutpostsApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import YAML from "yaml";
import { first } from "../../utils";

@customElement("ak-service-connection-kubernetes-form")
export class ServiceConnectionKubernetesForm extends Form<KubernetesServiceConnection> {

    set scUUID(value: string) {
        new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesRead({
            uuid: value,
        }).then(sc => {
            this.sc = sc;
        });
    }

    @property({attribute: false})
    sc?: KubernetesServiceConnection;

    getSuccessMessage(): string {
        if (this.sc) {
            return t`Successfully updated service-connection.`;
        } else {
            return t`Successfully created service-connection.`;
        }
    }

    send = (data: KubernetesServiceConnection): Promise<KubernetesServiceConnection> => {
        if (this.sc) {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesUpdate({
                uuid: this.sc.pk || "",
                data: data
            });
        } else {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsKubernetesCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.sc?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="local">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.sc?.local, false)}>
                    <label class="pf-c-check__label">
                        ${t`Local`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${t`If enabled, use the local connection. Required Docker socket/Kubernetes Integration.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Kubeconfig`}
                name="kubeconfig">
                <ak-codemirror mode="yaml" value="${YAML.stringify(this.sc?.kubeconfig)}">
                </ak-codemirror>
            </ak-form-element-horizontal>
        </form>`;
    }

}
