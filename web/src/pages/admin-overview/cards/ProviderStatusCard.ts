import { gettext } from "django";
import { customElement } from "lit-element";
import { ProvidersApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-card-provider")
export class ProviderStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return new ProvidersApi(DEFAULT_CONFIG).providersAllList({
            applicationIsnull: "true"
        }).then((value) => {
            return value.pagination.count;
        });
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value > 0) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: gettext("Warning: At least one Provider has no application assigned."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success"
            });
        }
    }

}
