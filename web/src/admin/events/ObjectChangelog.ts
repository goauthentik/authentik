import "#components/ak-event-info";
import "#elements/Tabs";
import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { aki } from "#common/api/client";
import { EventWithContext } from "#common/events";
import { actionToLabel } from "#common/labels";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { EventGeo, renderEventUser } from "#admin/events/utils";

import { Event, EventsApi } from "@goauthentik/api";
import { TruncateIPAddress } from "@goauthentik/truncator/ak-truncate-ip-address";

import { msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-object-changelog")
export class ObjectChangelog extends Table<Event> {
    public override expandable = true;

    public override order = "-created";

    @property()
    public targetModelPk!: string | number;

    @property()
    public targetModelApp?: string;

    @property()
    public targetModelName = "";

    protected override async apiEndpoint(): Promise<PaginatedResponse<Event>> {
        let modelName = this.targetModelName;
        let appName = this.targetModelApp;

        if (this.targetModelName.indexOf(".") !== -1) {
            const parts = this.targetModelName.split(".", 1);
            appName = parts[0];
            modelName = parts[1];
        }

        if (this.targetModelName === "") {
            return Promise.reject();
        }

        return aki(EventsApi).eventsEventsList({
            ...(await this.defaultEndpointConfig()),
            action: "model_",
            contextModelApp: appName,
            contextModelName: modelName,
            contextModelPk: this.targetModelPk.toString(),
        });
    }

    protected override rowLabel(item: Event): string {
        return actionToLabel(item.action);
    }

    protected columns: TableColumn[] = [
        [msg("Action"), "action"],
        [msg("User"), "enabled"],
        [msg("Creation Date"), "created"],
        [msg("Client IP"), "client_ip"],
    ];

    protected override willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("targetModelName") && this.targetModelName) {
            this.fetch();
        }
    }

    protected override row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            actionToLabel(item.action),
            renderEventUser(item),
            Timestamp(item.created),
            html`${TruncateIPAddress(item.clientIp)}<small>${EventGeo(item)}</small>`,
        ];
    }

    protected override renderExpanded(item: Event): SlottedTemplateResult {
        return html`<ak-event-info .event=${item as EventWithContext}></ak-event-info>`;
    }

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state
                ><span>${msg("No Events found.")}</span>
                <div slot="body">${msg("No matching events could be found.")}</div>
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-object-changelog": ObjectChangelog;
    }
}
