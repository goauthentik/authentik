import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { CryptoApi, CertificateKeyPair } from "authentik-api";

import "../../elements/forms/ModalForm";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteForm";
import "./CertificateKeyPairForm";
import "./CertificateGenerateForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-crypto-certificate-list")
export class CertificateKeyPairListPage extends TablePage<CertificateKeyPair> {
    expandable = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Certificate-Key Pairs");
    }
    pageDescription(): string {
        return gettext("Import certificates of external providers or create certificates to sign requests with.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-key";
    }

    @property()
    order = "name";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    apiEndpoint(page: number): Promise<AKResponse<CertificateKeyPair>> {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Private key available?"),
            new TableColumn("Expiry date"),
            new TableColumn(""),
        ];
    }

    row(item: CertificateKeyPair): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${gettext(item.privateKeyAvailable ? "Yes" : "No")}`,
            html`${item.certExpiry?.toLocaleString()}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext("Update Certificate-Key Pair")}
                </span>
                <ak-crypto-certificate-form slot="form" .keyPair=${item}>
                </ak-crypto-certificate-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Certificate-Key Pair")}
                .delete=${() => {
                    return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsDelete({
                        kpUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderExpanded(item: CertificateKeyPair): TemplateResult {
        return html`
        <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <dl class="pf-c-description-list pf-m-horizontal">
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${gettext("Certificate Fingerprint")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${item.fingerprint}</div>
                        </dd>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">
                            <span class="pf-c-description-list__text">${gettext("Certificate Subjet")}</span>
                        </dt>
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">${item.certSubject}</div>
                        </dd>
                    </div>
                </dl>
            </div>
        </td>
        <td></td>
        <td></td>`;
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Create")}
            </span>
            <span slot="header">
                ${gettext("Create Certificate-Key Pair")}
            </span>
            <ak-crypto-certificate-form slot="form">
            </ak-crypto-certificate-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Generate")}
            </span>
            <span slot="header">
                ${gettext("Generate Certificate-Key Pair")}
            </span>
            <ak-crypto-certificate-generate-form slot="form">
            </ak-crypto-certificate-generate-form>
            <button slot="trigger" class="pf-c-button pf-m-secondary">
                ${gettext("Generate")}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
