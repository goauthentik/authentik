import "#elements/forms/DeleteBulkForm";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { RotateSecretButton } from "#admin/secrets/RotateSecretButton";
import { SecretForm, secretTypeLabel } from "#admin/secrets/SecretForm";
import { SecretValueButton } from "#admin/secrets/SecretValueButton";

import { ModelEnum, Secret, SecretsApi, SecretTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-secret-list")
export class SecretListPage extends TablePage<Secret> {
    static styles = [...super.styles, PFBanner];

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for a secret name...", {
        id: "secret.list.search.placeholder",
    });

    protected override searchEnabled = true;

    public pageTitle = msg("Secrets", { id: "secret.verbose-name-plural" });
    public pageDescription = msg(
        "Credentials used by OAuth2/OpenID and Proxy providers. Each secret has its own permissions.",
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
            msg("Row Actions", { id: "secret.list.row-actions.label" }),
        ],
    ];

    protected override renderSectionBefore(): SlottedTemplateResult {
        return html`<div class="pf-c-banner pf-m-info">
            ${msg("Secrets are in preview.", { id: "secret.list.preview" })}
            <a href="mailto:hello+feature/secrets@goauthentik.io">${msg("Send us feedback!")}</a>
        </div>`;
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        const count = this.selectedElements.length;

        return html`<ak-forms-delete-bulk
            object-label=${
                count === 1
                    ? msg("Secret", { id: "secret.verbose-name" })
                    : msg("Secrets", { id: "secret.verbose-name-plural" })
            }
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
                ${msg("Delete", { id: "secret.list.delete.label" })}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: Secret): SlottedTemplateResult[] {
        return [
            html`<div>${item.name}</div>
                ${
                    item.managed
                        ? html`<small
                              >${msg("Managed by authentik", { id: "secret.list.managed.label" })}</small
                          >`
                        : nothing
                }`,
            html`${secretTypeLabel(item.type ?? SecretTypeEnum.Text)}`,
            html`<div>
                ${SecretValueButton(item)} ${IconEditButton(SecretForm, item.pk, item.name)}
                ${item.type === SecretTypeEnum.Text ? RotateSecretButton(item) : nothing}
                ${IconPermissionButton(item.name, {
                    model: ModelEnum.AuthentikCryptoSecretsSecret,
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
