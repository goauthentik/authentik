import "#elements/forms/DeleteBulkForm";

import { aki } from "#common/api/client";

import { IconRotateSecretButton } from "#elements/buttons/IconRotateSecretButton";
import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { SecretForm } from "#admin/secrets/SecretForm";
import { SecretValueButton } from "#admin/secrets/SecretValueButton";

import { ModelEnum, Secret, SecretsApi, SecretTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-secret-list")
export class SecretListPage extends TablePage<Secret> {
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for a secret name...", {
        id: "secret.list.search.placeholder",
    });

    protected override searchEnabled = true;

    public pageTitle = msg("Secrets", { id: "secret.list.title" });
    public pageDescription = msg(
        "Credentials used by providers, sources, stages, and connectors. Each secret has its own permissions.",
        { id: "secret.list.description" },
    );
    public pageIcon = "pf-icon pf-icon-key";

    public override order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Secret>> {
        return aki(SecretsApi).secretsSecretsList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name", { id: "secret.list.column.name" }), "name"],
        [msg("Type", { id: "secret.list.column.type" }), "type"],
        [
            msg("Actions", { id: "secret.list.column.actions" }),
            null,
            msg("Row Actions", { id: "secret.list.row-actions" }),
        ],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        const count = this.selectedElements.length;
        return html`<ak-forms-delete-bulk
            object-label=${count === 1
                ? msg("Secret", { id: "secret.verbose-name" })
                : msg("Secrets", { id: "secret.verbose-name-plural" })}
            .objects=${this.selectedElements}
            .metadata=${(item: Secret) => {
                return [{ key: msg("Name", { id: "secret.list.column.name" }), value: item.name }];
            }}
            .usedBy=${(item: Secret) => {
                return aki(SecretsApi).secretsSecretsUsedByList({
                    secretUuid: item.pk,
                });
            }}
            .delete=${(item: Secret) => {
                return aki(SecretsApi).secretsSecretsDestroy({
                    secretUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete", { id: "secret.list.delete" })}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected typeLabel(type?: SecretTypeEnum): string {
        switch (type) {
            case SecretTypeEnum.Multiline:
                return msg("Multi-line text", { id: "secret.type.multiline.label" });
            case SecretTypeEnum.File:
                return msg("File", { id: "secret.type.file.label" });
            default:
                return msg("Text", { id: "secret.type.text.label" });
        }
    }

    protected override row(item: Secret): SlottedTemplateResult[] {
        return [
            html`<div>${item.name}</div>
                ${item.managed
                    ? html`<small
                          >${msg("Managed by authentik", { id: "secret.list.managed" })}</small
                      >`
                    : nothing}`,
            html`${this.typeLabel(item.type)}`,
            html`<div>
                ${SecretValueButton(item)} ${IconEditButton(SecretForm, item.pk, item.name)}
                ${item.type === SecretTypeEnum.Text
                    ? IconRotateSecretButton({
                          rotate: () =>
                              aki(SecretsApi).secretsSecretsRotateCreate({ secretUuid: item.pk }),
                      })
                    : nothing}
                ${IconPermissionButton(item.name, {
                    model: ModelEnum.AuthentikSecretsSecret,
                    objectPk: item.pk,
                })}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(SecretForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-list": SecretListPage;
    }
}
