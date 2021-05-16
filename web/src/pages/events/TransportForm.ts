import { EventsApi, NotificationTransport, NotificationTransportModeEnum } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import { first } from "../../utils";
import { ModelForm } from "../../elements/forms/ModelForm";

@customElement("ak-event-transport-form")
export class TransportForm extends ModelForm<NotificationTransport, string> {

    loadInstance(pk: string): Promise<NotificationTransport> {
        return new EventsApi(DEFAULT_CONFIG).eventsTransportsRetrieve({
            uuid: pk,
        });
    }

    @property({type: Boolean})
    showWebhook = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated transport.`;
        } else {
            return t`Successfully created transport.`;
        }
    }

    send = (data: NotificationTransport): Promise<NotificationTransport> => {
        if (this.instance) {
            return new EventsApi(DEFAULT_CONFIG).eventsTransportsUpdate({
                uuid: this.instance.pk || "",
                data: data
            });
        } else {
            return new EventsApi(DEFAULT_CONFIG).eventsTransportsCreate({
                data: data
            });
        }
    };

    renderTransportModes(): TemplateResult {
        return html`
            <option value=${NotificationTransportModeEnum.Email} ?selected=${this.instance?.mode === NotificationTransportModeEnum.Email}>
                ${t`Email`}
            </option>
            <option value=${NotificationTransportModeEnum.Webhook} ?selected=${this.instance?.mode === NotificationTransportModeEnum.Webhook}>
                ${t`Webhook (generic)`}
            </option>
            <option value=${NotificationTransportModeEnum.WebhookSlack} ?selected=${this.instance?.mode === NotificationTransportModeEnum.WebhookSlack}>
                ${t`Webhook (Slack/Discord)`}
            </option>
        `;
    }

    firstUpdated(): void {
        if (this.instance) {
            this.onModeChange(this.instance.mode);
        }
    }

    onModeChange(mode: string): void {
        if (mode === NotificationTransportModeEnum.Webhook || mode === NotificationTransportModeEnum.WebhookSlack) {
            this.showWebhook = true;
        } else {
            this.showWebhook = false;
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.instance?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Mode`}
                ?required=${true}
                name="mode">
                <select class="pf-c-form-control" @change=${(ev: Event) => {
                    const current = (ev.target as HTMLInputElement).value;
                    this.onModeChange(current);
                }}>
                    ${this.renderTransportModes()}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                ?hidden=${!this.showWebhook}
                label=${t`Webhook URL`}
                name="webhookUrl">
                <input type="text" value="${ifDefined(this.instance?.webhookUrl)}" class="pf-c-form-control">
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="sendOnce">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.sendOnce, false)}>
                    <label class="pf-c-check__label">
                        ${t`Send once`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${t`Only send notification once, for example when sending a webhook into a chat channel.`}</p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
