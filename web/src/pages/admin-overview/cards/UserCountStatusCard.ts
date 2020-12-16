import { customElement } from "lit-element";
import { User } from "../../../api/Users";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-card-user-count")
export class UserCountStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return User.count();
    }

    getStatus(value: number): Promise<AdminStatus> {
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success"
        });
    }

}
