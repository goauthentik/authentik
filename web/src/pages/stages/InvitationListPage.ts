import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { Invitation } from "../../api/Invitations";

@customElement("ak-stage-invitation-list")
export class InvitationListPage extends TablePage<Invitation> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Invitations");
    }
    pageDescription(): string {
        return gettext("Create Invitation Links to enroll Users, and optionally force specific attributes of their account.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-migration");
    }

    @property()
    order = "expires";

    apiEndpoint(page: number): Promise<AKResponse<Invitation>> {
        return Invitation.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("ID", "pk"),
            new TableColumn("Created by", "created_by"),
            new TableColumn("Expiry"),
            new TableColumn(""),
        ];
    }

    row(item: Invitation): TemplateResult[] {
        return [
            html`${item.pk}`,
            html`${item.created_by.username}`,
            html`${new Date(item.expires * 1000).toLocaleString()}`,
            html`
            <ak-modal-button href="${Invitation.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${Invitation.adminUrl("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
