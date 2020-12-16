import { gettext } from "django";
import { customElement } from "lit-element";
import { DefaultClient, PBResponse } from "../../../api/Client";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";

@customElement("ak-admin-status-card-workers")
export class WorkersStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return DefaultClient.fetch<PBResponse<number>>(["admin", "workers"]).then((r) => {
            return r.pagination.count;
        });
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext("No workers connected. Background tasks will not run."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle"
            });
        }
    }

}
