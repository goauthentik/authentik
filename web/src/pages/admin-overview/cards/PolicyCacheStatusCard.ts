import { gettext } from "django";
import { customElement } from "lit-element";
import { TemplateResult, html } from "lit-html";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";
import "../../../elements/buttons/ModalButton";
import { PoliciesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";

@customElement("ak-admin-status-card-policy-cache")
export class PolicyCacheStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesAllCacheInfo({}).then((value) => {
            return value.count || 0;
        });
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: gettext("No policies cached. Users may experience slow response times."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success"
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
