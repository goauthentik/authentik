import { gettext } from "django";
import { customElement, html, TemplateResult } from "lit-element";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";
import "../../../elements/buttons/ModalButton";
import { FlowsApi } from "../../../api";
import { DEFAULT_CONFIG } from "../../../api/Config";

@customElement("ak-admin-status-card-flow-cache")
export class FlowCacheStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesCached({}).then((value) => {
            return value.count || 0;
        });
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: gettext("No flows cached."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success"
            });
        }
    }

    renderHeaderLink(): TemplateResult {
        return html`<ak-modal-button href="/administration/overview/cache/flow/">
            <a slot="trigger">
                <i class="fa fa-trash"> </i>
            </a>
            <div slot="modal"></div>
        </ak-modal-button>`;
    }

}
