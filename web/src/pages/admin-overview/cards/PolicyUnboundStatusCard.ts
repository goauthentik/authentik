import { gettext } from "django";
import { customElement } from "lit-element";
import { PoliciesApi } from "../../../api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-card-policy-unbound")
export class PolicyUnboundStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesAllList({
            bindingsIsnull: "true",
            promptstageIsnull: "true",
        }).then((value) => {
            return value.pagination.count;
        });
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value > 0) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: gettext("Policies without binding exist."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success"
            });
        }
    }

}
