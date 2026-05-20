import "#components/ak-hidden-text-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#admin/common/ak-crypto-certificate-search";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

import {
    EventsApi,
    NotificationTransport,
    NotificationWebhookMapping,
    PropertymappingsApi,
    PropertymappingsNotificationListRequest,
    StagesApi,
    TransportModeEnum,
    TypeCreate,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-event-transport-form")
export class TransportForm extends ModelForm<NotificationTransport, string> {
    public static override verboseName = msg("Notification Transport");
    public static override verboseNamePlural = msg("Notification Transports");

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
    async load(): Promise<void> {
        this.templates = await new StagesApi(DEFAULT_CONFIG).stagesEmailTemplatesList();
    }

    templates?: TypeCreate[];

    @property({ type: Boolean })
    showWebhook = false;

    @property({ type: Boolean })
    showEmail = false;

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated transport.")
            : msg("Successfully created transport.");
    }

    async send(data: NotificationTransport): Promise<NotificationTransport> {
        if (this.instance) {
            return new EventsApi(DEFAULT_CONFIG).eventsTransportsUpdate({
                uuid: this.instance.pk || "",
                notificationTransportRequest: data,
            });
        }
        return new EventsApi(DEFAULT_CONFIG).eventsTransportsCreate({
            notificationTransportRequest: data,
        });
    }

    onModeChange(mode: string | undefined): void {
        // Reset all flags
        this.showWebhook = false;
        this.showEmail = false;

        switch (mode) {
            case TransportModeEnum.Webhook:
            case TransportModeEnum.WebhookSlack:
                this.showWebhook = true;
                break;
            case TransportModeEnum.Email:
                this.showEmail = true;
                break;
            case TransportModeEnum.Local:
            default:
                // Both flags remain false
                break;
        }
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                label=${msg("Transport Name")}
                placeholder=${msg("Type a name for this transport...")}
                autofocus
                spellcheck="false"
                autocomplete="off"
                required
                name="name"
                value="${ifDefined(this.instance?.name)}"
            ></ak-text-input>
            <ak-switch-input
                name="sendOnce"
                label=${msg("Send once")}
                ?checked=${this.instance?.sendOnce ?? false}
                help=${msg(
                    "Only send notification once, for example when sending a webhook into a chat channel.",
                )}
            >
            </ak-switch-input>
            <ak-form-element-horizontal required name="mode">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "mode",
                        required: true,
                    },
                    msg("Mode"),
                )}
                <ak-radio
                    id="mode"
                    @change=${(ev: CustomEvent<{ value: TransportModeEnum }>) => {
                        this.onModeChange(ev.detail.value);
                    }}
                    .options=${[
                        {
                            label: msg("Local (notifications will be created within authentik)"),
                            value: TransportModeEnum.Local,
                            default: true,
                        },
                        {
                            label: msg("Email"),
                            value: TransportModeEnum.Email,
                        },
                        {
                            label: msg("Webhook (generic)"),
                            value: TransportModeEnum.Webhook,
                        },
                        {
                            label: msg("Webhook (Slack/Discord)"),
                            value: TransportModeEnum.WebhookSlack,
                        },
                    ]}
                    .value=${this.instance?.mode}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-hidden-text-input
                name="webhookUrl"
                label=${msg("Webhook URL")}
                value="${this.instance?.webhookUrl || ""}"
                input-hint="code"
                ?hidden=${!this.showWebhook}
                ?required=${this.showWebhook}
            >
            </ak-hidden-text-input>
            <ak-form-element-horizontal ?hidden=${!this.showWebhook} name="webhookCa">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "webhookCa",
                    },
                    msg("Webhook Certificate Authority"),
                )}
                <ak-crypto-certificate-search
                    id="webhookCa"
                    .certificate=${this.instance?.webhookCa}
                ></ak-crypto-certificate-search>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Keypair used to validate the certificate of the webhook endpoint. When not configured, the standard CA bundle is used.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal ?hidden=${!this.showWebhook} name="webhookMappingBody">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "webhookMappingBody",
                    },
                    msg("Webhook Body Mapping"),
                )}
                <ak-search-select
                    id="webhookMappingBody"
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
                    .renderElement=${(item: NotificationWebhookMapping) => item.name}
                    .value=${(item: NotificationWebhookMapping | null) => item?.pk}
                    .selected=${(item: NotificationWebhookMapping): boolean => {
                        return this.instance?.webhookMappingBody === item.pk;
                    }}
                    blankable
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal ?hidden=${!this.showWebhook} name="webhookMappingHeaders">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "webhookMappingHeaders",
                    },
                    msg("Webhook Header Mapping"),
                )}
                <ak-search-select
                    id="webhookMappingHeaders"
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
                    .value=${(item: NotificationWebhookMapping | null) => item?.pk}
                    .selected=${(item: NotificationWebhookMapping): boolean => {
                        return this.instance?.webhookMappingHeaders === item.pk;
                    }}
                    blankable
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                ?hidden=${!this.showEmail}
                ?required=${this.showEmail}
                name="emailSubjectPrefix"
            >
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "emailSubjectPrefix",
                        required: this.showEmail,
                    },
                    msg("Email Subject Prefix"),
                )}
                <input
                    id="emailSubjectPrefix"
                    type="text"
                    value="${this.instance?.emailSubjectPrefix || "authentik Notification: "}"
                    class="pf-c-form-control"
                    ?hidden=${!this.showEmail}
                    ?required=${this.showEmail}
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                ?hidden=${!this.showEmail}
                ?required=${this.showEmail}
                name="emailTemplate"
            >
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "emailTemplate",
                        required: this.showEmail,
                    },
                    msg("Email Template"),
                )}
                <select id="emailTemplate" name="users" class="pf-c-form-control">
                    ${this.templates?.map((template) => {
                        const selected =
                            this.instance?.emailTemplate === template.name ||
                            (!this.instance?.emailTemplate &&
                                template.name === "email/event_notification.html");
                        return html`<option value=${ifDefined(template.name)} ?selected=${selected}>
                            ${template.description}
                        </option>`;
                    })}
                </select>
            </ak-form-element-horizontal> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-transport-form": TransportForm;
    }
}
