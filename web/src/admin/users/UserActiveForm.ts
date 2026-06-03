import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/FormGroup";

import { DEFAULT_CONFIG } from "#common/api/config";
import { formatDisambiguatedUserDisplayName } from "#common/users";

import { modalInvoker } from "#elements/dialogs";
import { DestructiveModelForm } from "#elements/forms/DestructiveModelForm";
import { WithLocale } from "#elements/mixins/locale";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, UsedBy, User } from "@goauthentik/api";

import { str } from "@lit/localize";
import { msg } from "@lit/localize/init/install";
import { html } from "lit-html";
import { customElement } from "lit/decorators.js";

/**
 * A form for activating/deactivating a user.
 */
@customElement("ak-user-activation-toggle-form")
export class UserActivationToggleForm extends WithLocale(DestructiveModelForm<User>) {
    public static override verboseName = msg("User");
    public static override verboseNamePlural = msg("Users");

    protected coreAPI = new CoreApi(DEFAULT_CONFIG);

    protected override send(): Promise<unknown> {
        if (!this.instance) {
            return Promise.reject(new Error("No user instance provided"));
        }
        const nextActiveState = !this.instance.isActive;

        return this.coreAPI.coreUsersPartialUpdate({
            id: this.instance.pk,
            patchedUserRequest: {
                isActive: nextActiveState,
            },
        });
    }

    public override formatSubmitLabel(): string {
        return super.formatSubmitLabel(
            this.instance?.isActive ? msg("Deactivate") : msg("Activate"),
        );
    }

    public override formatSubmittingLabel(): string {
        return super.formatSubmittingLabel(
            this.instance?.isActive ? msg("Deactivating...") : msg("Activating..."),
        );
    }

    protected override formatDisplayName(): string {
        if (!this.instance) {
            return msg("Unknown user");
        }

        return formatDisambiguatedUserDisplayName(this.instance, this.activeLanguageTag);
    }

    protected override formatHeadline(): string {
        return this.instance?.isActive
            ? msg(str`Review ${this.verboseName} Deactivation`, {
                  id: "form.headline.deactivation",
              })
            : msg(str`Review ${this.verboseName} Activation`, { id: "form.headline.activation" });
    }

    public override usedBy = (): Promise<UsedBy[]> => {
        if (!this.instance) {
            return Promise.resolve([]);
        }

        return this.coreAPI.coreUsersUsedByList({ id: this.instance.pk });
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-activation-toggle-form": UserActivationToggleForm;
    }
}

export interface ToggleUserActivationButtonProps {
    className?: string;
}

export function ToggleUserActivationButton(
    user: User,
    { className = "" }: ToggleUserActivationButtonProps = {},
): SlottedTemplateResult {
    const label = user.isActive ? msg("Deactivate") : msg("Activate");
    const tooltip = user.isActive
        ? msg("Lock the user out of this system")
        : msg("Allow the user to log in and use this system");

    return html`<button
        class="pf-c-button pf-m-warning ${className}"
        type="button"
        ${modalInvoker(UserActivationToggleForm, {
            instance: user,
        })}
    >
        <pf-tooltip position="top" content=${tooltip}>${label}</pf-tooltip>
    </button>`;
}
