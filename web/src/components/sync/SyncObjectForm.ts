import "#elements/events/LogViewer";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-switch-input";
import { Form } from "#elements/forms/Form";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { groupSource, userSource } from "#admin/common/search-sources";

import {
    InitOverrideFunction,
    SyncObjectModelEnum,
    SyncObjectRequest,
    SyncObjectResult,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-sync-object-form")
export class SyncObjectForm extends Form<SyncObjectRequest> {
    @property({ type: Number })
    provider?: number;

    @property()
    model: SyncObjectModelEnum = SyncObjectModelEnum.UnknownDefaultOpenApi;

    @property({ attribute: false })
    result?: SyncObjectResult;

    @property({ attribute: false })
    sync: (
        requestParameters: {
            id: number;
            syncObjectRequest: SyncObjectRequest;
        },
        initOverrides?: RequestInit | InitOverrideFunction,
    ) => Promise<SyncObjectResult> = (_, __) => {
        return Promise.reject();
    };

    public override getSuccessMessage(): string {
        return msg("Successfully triggered sync.");
    }

    async send(data: SyncObjectRequest): Promise<void> {
        data.syncObjectModel = this.model;

        this.result = await this.sync({
            id: this.provider || 0,
            syncObjectRequest: data,
        });
    }

    renderSelectUser() {
        return html`<ak-form-element-horizontal label=${msg("User")} name="syncObjectId">
            ${AKSearchSelect({
                name: "syncObjectId",
                source: userSource,
                blankable: false,
            })}
        </ak-form-element-horizontal>`;
    }

    renderSelectGroup() {
        return html` <ak-form-element-horizontal label=${msg("Group")} name="syncObjectId">
            ${AKSearchSelect({
                name: "syncObjectId",
                source: groupSource,
                blankable: false,
            })}
        </ak-form-element-horizontal>`;
    }

    renderResult(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Log messages")}>
            <ak-log-viewer .items=${this.result?.messages}></ak-log-viewer>
        </ak-form-element-horizontal> `;
    }

    renderForm() {
        return html` ${
                this.model === SyncObjectModelEnum.AuthentikCoreModelsUser
                    ? this.renderSelectUser()
                    : nothing
            }
            ${
                this.model === SyncObjectModelEnum.AuthentikCoreModelsGroup
                    ? this.renderSelectGroup()
                    : nothing
            }
            <ak-switch-input
                name="overrideDryRun"
                label=${msg("Override dry-run mode")}
                help=${msg(
                    "When enabled, this sync will still execute mutating requests regardless of the dry-run mode in the provider.",
                )}
            ></ak-switch-input>
            ${this.result ? this.renderResult() : nothing}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sync-object-form": SyncObjectForm;
    }
}
