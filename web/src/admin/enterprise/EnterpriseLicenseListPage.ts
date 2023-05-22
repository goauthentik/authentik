import "@goauthentik/admin/enterprise/EnterpriseLicenseForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { EnterpriseApi, License } from "@goauthentik/api";

@customElement("ak-enterprise-license-list")
export class EnterpriseLicenseListPage extends TablePage<License> {
    checkbox = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Licenses`;
    }
    pageDescription(): string {
        // TODO: add copy text
        return t`TODO Copy`;
    }
    pageIcon(): string {
        // TODO: update icon
        return "pf-icon pf-icon-key";
    }

    @property()
    order = "name";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<License>> {
        return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Users`),
            new TableColumn(t`Expiry date`),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`License(s)`}
            .objects=${this.selectedElements}
            .metadata=${(item: License) => {
                return [
                    { key: t`Name`, value: item.name },
                    { key: t`Expiry`, value: item.expiry?.toLocaleString() },
                ];
            }}
            .usedBy=${(item: License) => {
                return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseUsedByList({
                    licenseUuid: item.licenseUuid,
                });
            }}
            .delete=${(item: License) => {
                return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseDestroy({
                    licenseUuid: item.licenseUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: License): TemplateResult[] {
        let color = PFColor.Green;
        if (item.expiry) {
            const now = new Date();
            const inAMonth = new Date();
            inAMonth.setDate(inAMonth.getDate() + 30);
            if (item.expiry <= inAMonth) {
                color = PFColor.Orange;
            }
            if (item.expiry <= now) {
                color = PFColor.Red;
            }
        }
        return [
            html`<div>${item.name}</div>`,
            html`<div>
                <small>0 / ${item.users}</small>
                <small>0 / ${item.externalUsers}</small>
            </div>`,
            html`<ak-label color=${color}> ${item.expiry?.toLocaleString()} </ak-label>`,
            html`<ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update License`} </span>
                <ak-enterprise-license-form slot="form" .instancePk=${item.licenseUuid}>
                </ak-enterprise-license-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create License`} </span>
                <ak-enterprise-license-form slot="form"> </ak-enterprise-license-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
        `;
    }
}
