import { EventsApi, NotificationTransport, NotificationTransportModeEnum } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-event-transport-form")
export class TransportForm extends Form<NotificationTransport> {

    @property({attribute: false})
    transport?: NotificationTransport;

    @property({type: Boolean})
    showWebhook = false;

    getSuccessMessage(): string {
        if (this.transport) {
            return gettext("Successfully updated transport.");
        } else {
            return gettext("Successfully created transport.");
        }
    }

    send = (data: NotificationTransport): Promise<NotificationTransport> => {
        if (this.transport) {
            return new EventsApi(DEFAULT_CONFIG).eventsTransportsUpdate({
                uuid: this.transport.pk || "",
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
            <option value=${NotificationTransportModeEnum.Email} ?selected=${this.transport?.mode === NotificationTransportModeEnum.Email}>
                ${gettext("Email")}
            </option>
            <option value=${NotificationTransportModeEnum.Webhook} ?selected=${this.transport?.mode === NotificationTransportModeEnum.Webhook}>
                ${gettext("Webhook (generic)")}
            </option>
            <option value=${NotificationTransportModeEnum.WebhookSlack} ?selected=${this.transport?.mode === NotificationTransportModeEnum.WebhookSlack}>
                ${gettext("Webhook (Slack/Discord)")}
            </option>
        `;
    }

    firstUpdated(): void {
        if (this.transport) {
            this.onModeChange(this.transport.mode);
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
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.transport?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Mode")}
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
                label=${gettext("Webhook URL")}
                name="webhookUrl">
                <input type="text" value="${ifDefined(this.transport?.webhookUrl)}" class="pf-c-form-control">
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="sendOnce">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.transport?.sendOnce || false}>
                    <label class="pf-c-check__label">
                        ${gettext("Send once")}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${gettext("Only send notification once, for example when sending a webhook into a chat channel.")}</p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
