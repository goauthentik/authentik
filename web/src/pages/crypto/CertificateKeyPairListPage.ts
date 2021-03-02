import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { CertificateKeyPair } from "../../api/CertificateKeyPair";
import { PAGE_SIZE } from "../../constants";

@customElement("ak-crypto-certificatekeypair-list")
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
        return gettext("pf-icon pf-icon-key");
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<CertificateKeyPair>> {
        return CertificateKeyPair.list({
            ordering: this.order,
            page: page,
            page_size: PAGE_SIZE,
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
            html`${gettext(item.private_key_available ? "Yes" : "No")}`,
            html`${new Date(item.cert_expiry * 1000).toLocaleString()}`,
            html`
            <ak-modal-button href="${CertificateKeyPair.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${CertificateKeyPair.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
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
                                <div class="pf-c-description-list__text">${item.cert_subject}</div>
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
        <ak-modal-button href=${CertificateKeyPair.adminUrl("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        <ak-modal-button href=${CertificateKeyPair.adminUrl("generate/")}>
            <ak-spinner-button slot="trigger" class="pf-m-secondary">
                ${gettext("Generate")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
