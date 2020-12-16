import { gettext } from "django";
import { customElement } from "lit-element";
import { Policy } from "../../../api/Policies";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-card-policy-unbound")
export class PolicyUnboundStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return Policy.list({
            "bindings__isnull": true,
            "promptstage__isnull": true,
        }).then((response) => {
            return response.pagination.count;
        });
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value > 0) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext("Policies without binding exist."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle"
            });
        }
    }

}
