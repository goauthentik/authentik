import "#admin/rbac/ObjectPermissionModal";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#components/ak-status-label";

import { aki } from "#common/api/client";

import { IconEditButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { ObjectAttributeForm } from "#admin/object-attributes/ObjectAttributeForm";

import { CoreApi, ObjectAttribute, ObjectAttributeTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

export function formatObjectAttributeType(type?: ObjectAttributeTypeEnum): string {
    if (!type) return "";

    switch (type) {
        case ObjectAttributeTypeEnum.Text:
            return msg("Text");
        case ObjectAttributeTypeEnum.Number:
            return msg("Number");
        case ObjectAttributeTypeEnum.Boolean:
            return msg("Boolean");
    }

    return msg("Unknown type");
}

@customElement("ak-object-attribute-list")
export class ObjectAttributeListPage extends TablePage<ObjectAttribute> {
    protected override searchEnabled = true;
    protected override rowLabel(item: ObjectAttribute): string | null {
        return item.pk ?? null;
    }

    public pageTitle = msg("Object attributes");
    public pageDescription = "Configure attributes on objects such as users and groups.";
    public pageIcon = "pf-icon pf-icon-flavor";

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "key";

    protected override async apiEndpoint(): Promise<PaginatedResponse<ObjectAttribute>> {
        return aki(CoreApi).coreObjectAttributesList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Label"), "label"],
        [msg("Type"), "type"],
        [msg("Enabled"), "enabled"],
        [msg("Object type"), "object_type"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        return html`<ak-forms-delete-bulk
            object-label=${msg("Object Attribute(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: ObjectAttribute) => {
                return [
                    { key: msg("Object type"), value: item.objectTypeObj.verboseNamePlural },
                    { key: msg("Label"), value: item.label },
                    { key: msg("Key"), value: item.key },
                ];
            }}
            .delete=${(item: ObjectAttribute) => {
                return aki(CoreApi).coreObjectAttributesDestroy({
                    attributeId: item.pk,
                });
            }}
        >
            <button
                ?disabled=${!this.selectedElements.length}
                slot="trigger"
                class="pf-c-button pf-m-danger"
            >
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return html`<ak-forms-modal>
            <span slot="submit">${msg("Create")}</span>
            <span slot="header">${msg("New Attribute")}</span>
            <ak-object-attribute-form slot="form"> </ak-object-attribute-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
        </ak-forms-modal>`;
    }

    protected override row(item: ObjectAttribute): SlottedTemplateResult[] {
        return [
            html`<div>
                <div>${item.group ? html`${item.group}: ${item.label}` : html`${item.label}`}</div>
                <code>${item.key}</code>
            </div>`,
            html`${formatObjectAttributeType(item.type)}`,
            html`<ak-status-label ?good=${item.enabled} type="info"></ak-status-label>`,
            html`${item.objectTypeObj.verboseNamePlural}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(ObjectAttributeForm, item.pk, item.label)}
            </div>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-object-attribute-list": ObjectAttributeListPage;
    }
}
