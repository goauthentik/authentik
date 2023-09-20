import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-toggle-group";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import {
    CoreApi,
    CoreUsersListRequest,
    ModelEnum,
    User,
    UserAssignedObjectPermission,
} from "@goauthentik/api";

@customElement("ak-rbac-user-object-permission-form")
export class UserObjectPermissionForm extends ModelForm<UserAssignedObjectPermission, number> {
    loadInstance(): Promise<UserAssignedObjectPermission> {
        throw new Error("Method not implemented.");
    }

    getSuccessMessage(): string {
        return msg("Successfully assigned permission.");
    }

    send(data: UserAssignedObjectPermission): Promise<unknown> {
        return new CoreApi(DEFAULT_CONFIG).coreRbacUserAssignCreate({
            id: 0,
            userAssignRequest: {
                permissions: [],
                model: ModelEnum.BlueprintsBlueprintinstance,
                objectPk: "",
            },
        });
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("User")} name="user">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(args);
                        return users.results;
                    }}
                    .renderElement=${(user: User): string => {
                        return user.username;
                    }}
                    .renderDescription=${(user: User): TemplateResult => {
                        return html`${user.name}`;
                    }}
                    .value=${(user: User | undefined): number | undefined => {
                        return user?.pk;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
        </form>`;
    }
}
