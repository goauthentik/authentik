import "#elements/forms/HorizontalFormElement";
import "#components/ak-radio-input";
import "#components/ak-switch-input";

import { aki } from "#common/api/client";
import { dateTimeLocal } from "#common/temporal";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

import {
    Action0beEnum,
    LifecycleApi,
    UserOffboarding,
    UserOffboardingRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

// Default the scheduled time to one day out.
const DEFAULT_OFFSET = 24 * 60 * 60 * 1000;

/**
 * Schedule the deactivation or deletion of a single user at an absolute time.
 *
 * @prop {number} userId - The primary key of the user to offboard.
 */
@customElement("ak-user-offboarding-form")
export class UserOffboardingForm extends ModelForm<UserOffboarding, string> {
    public static override verboseName = msg("User Offboarding");
    public static override verboseNamePlural = msg("User Offboardings");

    #api = aki(LifecycleApi);

    @property({ type: Number, attribute: "user-id" })
    public userId?: number;

    @state()
    protected scheduledFor: Date = new Date(Date.now() + DEFAULT_OFFSET);

    protected scheduledMinimumDate = new Date();

    async loadInstance(pk: string): Promise<UserOffboarding> {
        return this.#api.lifecycleUserOffboardingRetrieve({ id: pk });
    }

    public override getSuccessMessage(): string {
        return msg("Successfully scheduled offboarding.");
    }

    protected override async send(data: UserOffboarding): Promise<UserOffboarding> {
        const request = {
            ...data,
            user: this.userId,
        } as unknown as UserOffboardingRequest;

        return this.#api.lifecycleUserOffboardingCreate({
            userOffboardingRequest: request,
        });
    }

    protected override renderForm() {
        return html`<ak-radio-input
                name="action"
                label=${msg("Action")}
                .value=${Action0beEnum.Deactivate}
                .options=${[
                    {
                        label: msg("Deactivate"),
                        value: Action0beEnum.Deactivate,
                        default: true,
                        description: html`${msg(
                            "Lock the user out of authentik without removing their account.",
                        )}`,
                    },
                    {
                        label: msg("Delete"),
                        value: Action0beEnum.Delete,
                        description: html`${msg("Permanently delete the user's account.")}`,
                    },
                ]}
            ></ak-radio-input>

            <ak-form-element-horizontal name="scheduledFor" required>
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "offboarding-date-input",
                    },
                    msg("Scheduled for"),
                )}
                <input
                    id="offboarding-date-input"
                    type="datetime-local"
                    value=${dateTimeLocal(this.scheduledFor)}
                    min=${dateTimeLocal(this.scheduledMinimumDate)}
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg("The offboarding action runs at this time.")}
                </p>
            </ak-form-element-horizontal>

            <ak-switch-input
                name="revokeSessions"
                label=${msg("Revoke sessions")}
                ?checked=${true}
                help=${msg("Revoke all of the user's sessions when offboarding.")}
            ></ak-switch-input>

            <ak-switch-input
                name="revokeTokens"
                label=${msg("Revoke tokens")}
                ?checked=${true}
                help=${msg("Revoke all of the user's tokens when offboarding.")}
            ></ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-offboarding-form": UserOffboardingForm;
    }
}
