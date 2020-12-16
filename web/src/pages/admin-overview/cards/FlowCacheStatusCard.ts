import { gettext } from "django";
import { customElement, html, TemplateResult } from "lit-element";
import { Flow } from "../../../api/flow";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";
import "../../../elements/buttons/ModalButton";

@customElement("ak-admin-status-card-flow-cache")
export class FlowCacheStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return Flow.cached();
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext("No flows cached."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle"
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
