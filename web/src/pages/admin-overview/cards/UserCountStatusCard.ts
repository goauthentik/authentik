import { customElement } from "lit-element";
import { CoreApi } from "../../../api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-card-user-count")
export class UserCountStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            pageSize: 1
        }).then((value) => {
            return value.pagination.count;
        });
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    getStatus(value: number): Promise<AdminStatus> {
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success"
        });
    }

}
