import { t } from "@lingui/macro";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { CryptoApi, CertificateKeyPair } from "@goauthentik/api";

import "../../elements/forms/ModalForm";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteBulkForm";
import "./CertificateKeyPairForm";
import "./CertificateGenerateForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-crypto-certificate-list")
export class CertificateKeyPairListPage extends TablePage<CertificateKeyPair> {
    expandable = true;
    checkbox = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Certificate-Key Pairs`;
    }
    pageDescription(): string {
        return t`Import certificates of external providers or create certificates to sign requests with.`;
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
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Private key available?`),
            new TableColumn(t`Expiry date`),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Certificate-Key Pair(s)`}
            .objects=${this.selectedElements}
            .metadata=${(item: CertificateKeyPair) => {
                return [
                    { key: t`Name`, value: item.name },
                    { key: t`Expiry`, value: item.certExpiry.toLocaleString() },
                ];
            }}
            .usedBy=${(item: CertificateKeyPair) => {
                return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsUsedByList({
                    kpUuid: item.pk,
                });
            }}
            .delete=${(item: CertificateKeyPair) => {
                return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsDestroy({
                    kpUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: CertificateKeyPair): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.privateKeyAvailable ? t`Yes` : t`No`}`,
            html`${item.certExpiry?.toLocaleString()}`,
            html` <ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update Certificate-Key Pair`} </span>
                <ak-crypto-certificate-form slot="form" .instancePk=${item.pk}>
                </ak-crypto-certificate-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderExpanded(item: CertificateKeyPair): TemplateResult {
        return html`<td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${t`Certificate Fingerprint (SHA1)`}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.fingerprintSha1}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${t`Certificate Fingerprint (SHA256)`}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.fingerprintSha256}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${t`Certificate Subjet`}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">${item.certSubject}</div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Download`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    <a
                                        class="pf-c-button pf-m-secondary"
                                        target="_blank"
                                        href=${item.certificateDownloadUrl}
                                    >
                                        ${t`Download Certificate`}
                                    </a>
                                    ${item.privateKeyAvailable
                                        ? html`<a
                                              class="pf-c-button pf-m-secondary"
                                              target="_blank"
                                              href=${item.privateKeyDownloadUrl}
                                          >
                                              ${t`Download Private key`}
                                          </a>`
                                        : html``}
                                </div>
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
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Certificate-Key Pair`} </span>
                <ak-crypto-certificate-form slot="form"> </ak-crypto-certificate-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            <ak-forms-modal>
                <span slot="submit"> ${t`Generate`} </span>
                <span slot="header"> ${t`Generate Certificate-Key Pair`} </span>
                <ak-crypto-certificate-generate-form slot="form">
                </ak-crypto-certificate-generate-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">${t`Generate`}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}
