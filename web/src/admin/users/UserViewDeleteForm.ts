import { UserDeleteForm } from "#elements/user/utils";

import { customElement } from "lit/decorators.js";

@customElement("ak-user-view-delete-form")
export class UserViewDeleteForm extends UserDeleteForm {
    onSuccess(): void {
        super.onSuccess();
        // Navigate to user list after successful deletion
        window.location.hash = "#/identity/users";
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-view-delete-form": UserViewDeleteForm;
    }
}
