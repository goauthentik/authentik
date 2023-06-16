import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    EventsApi,
    NotificationTransport,
    NotificationTransportModeEnum,
    NotificationWebhookMapping,
    PropertymappingsApi,
    PropertymappingsNotificationListRequest,
} from "@goauthentik/api";

@customElement("ak-event-transport-form")
export class TransportForm extends ModelForm<NotificationTransport, string> {
    loadInstance(pk: string): Promise<NotificationTransport> {
        return new EventsApi(DEFAULT_CONFIG)
            .eventsTransportsRetrieve({
                uuid: pk,
            })
            .then((transport) => {
                this.onModeChange(transport.mode);
                return transport;
            });
    }

    @property({ type: Boolean })
    showWebhook = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated transport.");
        } else {
            return msg("Successfully created transport.");
        }
    }

    async send(data: NotificationTransport): Promise<NotificationTransport> {
        if (this.instance) {
            return new EventsApi(DEFAULT_CONFIG).eventsTransportsUpdate({
                uuid: this.instance.pk || "",
                notificationTransportRequest: data,
            });
        } else {
            return new EventsApi(DEFAULT_CONFIG).eventsTransportsCreate({
                notificationTransportRequest: data,
            });
        }
    }

    onModeChange(mode: string | undefined): void {
        if (
            mode === NotificationTransportModeEnum.Webhook ||
            mode === NotificationTransportModeEnum.WebhookSlack
        ) {
            this.showWebhook = true;
        } else {
            this.showWebhook = false;
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Mode")} ?required=${true} name="mode">
                <ak-radio
                    @change=${(ev: CustomEvent<NotificationTransportModeEnum>) => {
                        this.onModeChange(ev.detail);
                    }}
                    .options=${[
                        {
                            label: msg("Local (notifications will be created within authentik)"),
                            value: NotificationTransportModeEnum.Local,
                            default: true,
                        },
                        {
                            label: msg("Email"),
                            value: NotificationTransportModeEnum.Email,
                        },
                        {
                            label: msg("Webhook (generic)"),
                            value: NotificationTransportModeEnum.Webhook,
                        },
                        {
                            label: msg("Webhook (Slack/Discord)"),
                            value: NotificationTransportModeEnum.WebhookSlack,
                        },
                    ]}
                    .value=${this.instance?.mode}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                ?hidden=${!this.showWebhook}
                label=${msg("Webhook URL")}
                name="webhookUrl"
                ?required=${true}
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.webhookUrl)}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                ?hidden=${!this.showWebhook}
                label=${msg("Webhook Mapping")}
                name="webhookMapping"
            >
                <ak-search-select
                    .fetchObjects=${async (
                        query?: string,
                    ): Promise<NotificationWebhookMapping[]> => {
                        const args: PropertymappingsNotificationListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const items = await new PropertymappingsApi(
                            DEFAULT_CONFIG,
                        ).propertymappingsNotificationList(args);
                        return items.results;
                    }}
                    .renderElement=${(item: NotificationWebhookMapping): string => {
                        return item.name;
                    }}
                    .value=${(item: NotificationWebhookMapping | undefined): string | undefined => {
                        return item?.pk;
                    }}
                    .selected=${(item: NotificationWebhookMapping): boolean => {
                        return this.instance?.webhookMapping === item.pk;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="sendOnce">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.sendOnce, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Send once")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Only send notification once, for example when sending a webhook into a chat channel.",
                    )}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
