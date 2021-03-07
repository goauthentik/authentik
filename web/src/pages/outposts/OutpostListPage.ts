import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { AKResponse } from "../../api/Client";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";

import "./OutpostHealth";
import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/TokenCopyButton";
import { PAGE_SIZE } from "../../constants";
import { Outpost, OutpostsApi } from "../../api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-outpost-list")
export class OutpostListPage extends TablePage<Outpost> {
    pageTitle(): string {
        return "Outposts";
    }
    pageDescription(): string | undefined {
        return "Outposts are deployments of authentik components to support different environments and protocols, like reverse proxies.";
    }
    pageIcon(): string {
        return "pf-icon pf-icon-zone";
    }
    searchEnabled(): boolean {
        return true;
    }
    apiEndpoint(page: number): Promise<AKResponse<Outpost>> {
        return new OutpostsApi(DEFAULT_CONFIG).outpostsOutpostsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }
    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Providers"),
            new TableColumn("Health and Version"),
            new TableColumn(""),
        ];
    }

    @property()
    order = "name";

    row(item: Outpost): TemplateResult[] {
        return [
            html`${item.name}`,
            html`<ul>${item.providersObj?.map((p) => {
                return html`<li><a href="#/core/providers/${p.pk}">${p.name}</a></li>`;
            })}</ul>`,
            html`<ak-outpost-health outpostId=${ifDefined(item.pk)}></ak-outpost-health>`,
            html`
            <ak-modal-button href="${AdminURLManager.outposts(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>&nbsp;
            <ak-modal-button href="${AdminURLManager.outposts(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button>
                <button slot="trigger" class="pf-c-button pf-m-tertiary">
                    ${gettext("View Deployment Info")}
                </button>
                <div slot="modal">
                    <div class="pf-c-modal-box__header">
                        <h1 class="pf-c-title pf-m-2xl" id="modal-title">${gettext("Outpost Deployment Info")}</h1>
                    </div>
                    <div class="pf-c-modal-box__body" id="modal-description">
                        <p><a href="https://goauthentik.io/docs/outposts/outposts/#deploy">${gettext("View deployment documentation")}</a></p>
                        <form class="pf-c-form">
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label" for="help-text-simple-form-name">
                                    <span class="pf-c-form__label-text">AUTHENTIK_HOST</span>
                                </label>
                                <input class="pf-c-form-control" readonly type="text" value="${document.location.toString()}" />
                            </div>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label" for="help-text-simple-form-name">
                                    <span class="pf-c-form__label-text">AUTHENTIK_TOKEN</span>
                                </label>
                                <div>
                                    <ak-token-copy-button identifier="${ifDefined(item.tokenIdentifier)}">
                                        ${gettext("Click to copy token")}
                                    </ak-token-copy-button>
                                </div>
                            </div>
                            <h3>${gettext("If your authentik Instance is using a self-signed certificate, set this value.")}</h3>
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label" for="help-text-simple-form-name">
                                    <span class="pf-c-form__label-text">AUTHENTIK_INSECURE</span>
                                </label>
                                <input class="pf-c-form-control" readonly type="text" value="true" />
                            </div>
                        </form>
                    </div>
                    <footer class="pf-c-modal-box__footer pf-m-align-left">
                        <a class="pf-c-button pf-m-primary">${gettext("Close")}</a>
                    </footer>
                </div>
            </ak-modal-button>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${AdminURLManager.outposts("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
