import "#components/ak-event-info";
import "#elements/Tabs";
import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { EventGeo, renderEventUser } from "#common/events/utils";
import { actionToLabel } from "#common/labels";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Event, EventsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-object-changelog")
export class ObjectChangelog extends Table<Event> {
    expandable = true;

    @property()
    order = "-created";

    @property()
    targetModelPk!: string | number;

    @property()
    targetModelApp?: string;

    @property()
    targetModelName = "";

    async apiEndpoint(): Promise<PaginatedResponse<Event>> {
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
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
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

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("targetModelName") && this.targetModelName) {
            this.fetch();
        }
    }

    row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            html`${actionToLabel(item.action)}`,
            renderEventUser(item),
            Timestamp(item.created),
            html`<div>${item.clientIp || msg("-")}</div>
                <small>${EventGeo(item)}</small>`,
        ];
    }

    renderExpanded(item: Event): TemplateResult {
        return html`<ak-event-info .event=${item as EventWithContext}></ak-event-info>`;
    }

    renderEmpty(): TemplateResult {
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
