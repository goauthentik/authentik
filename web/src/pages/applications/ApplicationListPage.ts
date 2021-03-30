import { gettext } from "django";
import { css, CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/forms/ModalForm";
import "../../elements/forms/DeleteForm";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { Application, CoreApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import "./ApplicationForm";

@customElement("ak-application-list")
export class ApplicationListPage extends TablePage<Application> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Applications");
    }
    pageDescription(): string {
        return gettext("External Applications which use authentik as Identity-Provider, utilizing protocols like OAuth2 and SAML.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-applications";
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<Application>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(PFAvatar, css`
            tr td:first-child {
                width: auto;
                min-width: 0px;
                text-align: center;
                vertical-align: middle;
            }
        `);
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(""),
            new TableColumn("Name", "name"),
            new TableColumn("Slug", "slug"),
            new TableColumn("Provider"),
            new TableColumn("Provider Type"),
            new TableColumn(""),
        ];
    }

    row(item: Application): TemplateResult[] {
        return [
            item.metaIcon ?
                html`<img class="app-icon pf-c-avatar" src="${item.metaIcon}" alt="${gettext("Application Icon")}">` :
                html`<i class="fas fas fa-share-square"></i>`,
            html`<a href="#/core/applications/${item.slug}">
                <div>
                    ${item.name}
                </div>
                ${item.metaPublisher ? html`<small>${item.metaPublisher}</small>` : html``}
            </a>`,
            html`<code>${item.slug}</code>`,
            html`${item.provider?.name || "-"}`,
            html`${item.provider?.verboseName || "-"}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext("Update Application")}
                </span>
                <ak-application-form slot="form" .application=${item}>
                </ak-application-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Application")}
                .delete=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreApplicationsDelete({
                        slug: item.slug || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Create")}
            </span>
            <span slot="header">
                ${gettext("Create Application")}
            </span>
            <ak-application-form slot="form">
            </ak-application-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
