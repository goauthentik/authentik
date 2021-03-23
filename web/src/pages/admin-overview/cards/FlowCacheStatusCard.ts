import { gettext } from "django";
import { customElement, html, TemplateResult } from "lit-element";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";
import { FlowsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/ConfirmationForm";

@customElement("ak-admin-status-card-flow-cache")
export class FlowCacheStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesCacheInfo({}).then((value) => {
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
        return html`<ak-forms-confirm
                successMessage="Successfully cleared flow cache"
                errorMessage="Failed to delete flow cache"
                action="Clear cache"
                .onConfirm=${() => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsInstancesCacheClear();
                }}>
                <span slot="header">
                    ${gettext("Clear Flow cache")}
                </span>
                <p slot="body">
                    ${gettext(`Are you sure you want to clear the flow cache?
                        This will cause all flows to be re-evaluated on their next usage.`)}
                </p>
                <a slot="trigger">
                    <i class="fa fa-trash"> </i>
                </a>
                <div slot="modal"></div>
            </ak-forms-confirm>`;
    }

}
