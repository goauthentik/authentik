import { gettext } from "django";
import { customElement } from "lit-element";
import { TemplateResult, html } from "lit-html";
import { Policy } from "../../../api/policy";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";
import "../../../elements/buttons/ModalButton";

@customElement("ak-admin-status-card-policy-cache")
export class PolicyCacheStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return Policy.cached();
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext("No policies cached. Users may experience slow response times."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle"
            });
        }
    }

    renderHeaderLink(): TemplateResult {
        return html`<ak-modal-button href="/administration/overview/cache/policy/">
            <a slot="trigger">
                <i class="fa fa-trash"> </i>
            </a>
            <div slot="modal"></div>
        </ak-modal-button>`;
    }

}
