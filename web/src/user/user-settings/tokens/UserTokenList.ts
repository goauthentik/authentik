import { IntentToLabel } from "@goauthentik/admin/tokens/TokenListPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/Dropdown";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/TokenCopyButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";
import "@goauthentik/user/user-settings/tokens/UserTokenForm";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { CoreApi, IntentEnum, Token } from "@goauthentik/api";

@customElement("ak-user-token-list")
export class UserTokenList extends Table<Token> {
    searchEnabled(): boolean {
        return true;
    }

    expandable = true;
    checkbox = true;

    @property()
    order = "expires";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Token>> {
        return new CoreApi(DEFAULT_CONFIG).coreTokensList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            managed: "",
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(t`Identifier`, "identifier"), new TableColumn("")];
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Token`} </span>
                <ak-user-token-form intent=${IntentEnum.Api} slot="form"> </ak-user-token-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Create Token`}
                </button>
            </ak-forms-modal>
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create App password`} </span>
                <ak-user-token-form intent=${IntentEnum.AppPassword} slot="form">
                </ak-user-token-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Create App password`}
                </button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }

    renderExpanded(item: Token): TemplateResult {
        return html` <td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`User`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.userObj?.username}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Expiring`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    <ak-label color=${item.expiring ? PFColor.Green : PFColor.Red}>
                                        ${item.expiring ? t`Yes` : t`No`}
                                    </ak-label>
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Expiring`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.expiring ? item.expires?.toLocaleString() : t`-`}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Intent`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${IntentToLabel(item.intent || IntentEnum.Api)}
                                </div>
                            </dd>
                        </div>
                    </dl>
                </div>
            </td>
            <td></td>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Token(s)`}
            .objects=${this.selectedElements}
            .delete=${(item: Token) => {
                return new CoreApi(DEFAULT_CONFIG).coreTokensDestroy({
                    identifier: item.identifier,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Token): TemplateResult[] {
        return [
            html`${item.identifier}`,
            html`
                <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Token`} </span>
                    <ak-user-token-form slot="form" .instancePk=${item.identifier}>
                    </ak-user-token-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                <ak-token-copy-button
                    class="pf-c-button pf-m-plain"
                    identifier="${item.identifier}"
                >
                    <i class="fas fa-copy"></i>
                </ak-token-copy-button>
            `,
        ];
    }
}
