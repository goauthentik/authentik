import { NotificationWebhookMapping, PropertymappingsApi } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import { ModelForm } from "../../elements/forms/ModelForm";

@customElement("ak-property-mapping-notification-form")
export class PropertyMappingNotification extends ModelForm<NotificationWebhookMapping, string> {
    loadInstance(pk: string): Promise<NotificationWebhookMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsNotificationRetrieveRaw({
            pmUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated mapping.`;
        } else {
            return t`Successfully created mapping.`;
        }
    }

    send = (data: NotificationWebhookMapping): Promise<NotificationWebhookMapping> => {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsNotificationUpdate({
                pmUuid: this.instance.pk || "",
                notificationWebhookMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsNotificationCreate({
                notificationWebhookMappingRequest: data,
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
            <ak-form-element-horizontal label=${t`Expression`} ?required=${true} name="expression">
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.expression)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Expression using Python.`}
                    <a
                        target="_blank"
                        href="https://goauthentik.io/docs/property-mappings/expression/"
                    >
                        ${t`See documentation for a list of all variables.`}
                    </a>
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
