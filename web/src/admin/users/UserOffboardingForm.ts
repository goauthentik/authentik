import "#elements/forms/HorizontalFormElement";
import "#components/ak-radio-input";
import "#components/ak-switch-input";

import { aki } from "#common/api/client";
import { dateTimeLocal } from "#common/temporal";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

import {
    LifecycleApi,
    OffboardingActionEnum,
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
    public static override verboseName = msg("User Offboarding", {
        id: "offboarding.form.verbose-name",
    });
    public static override verboseNamePlural = msg("User Offboardings", {
        id: "offboarding.form.verbose-name-plural",
    });

    #api = aki(LifecycleApi);

    @property({ type: Number, attribute: "user-id" })
    public userId?: number;

    @state()
    protected scheduledAt: Date = new Date(Date.now() + DEFAULT_OFFSET);

    protected scheduledMinimumDate = new Date();

    async loadInstance(pk: string): Promise<UserOffboarding> {
        return this.#api.lifecycleUserOffboardingRetrieve({ id: pk });
    }

    public override getSuccessMessage(): string {
        return msg("Successfully scheduled offboarding.", { id: "offboarding.schedule.success" });
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
                label=${msg("Action", { id: "offboarding.field.action.label" })}
                .value=${OffboardingActionEnum.Deactivate}
                .options=${[
                    {
                        label: msg("Deactivate", { id: "offboarding.action.deactivate.label" }),
                        value: OffboardingActionEnum.Deactivate,
                        default: true,
                        description: html`${msg(
                            "Lock the user out of authentik without removing their account.",
                            { id: "offboarding.action.deactivate.description" },
                        )}`,
                    },
                    {
                        label: msg("Delete", { id: "offboarding.action.delete.label" }),
                        value: OffboardingActionEnum.Delete,
                        description: html`${msg("Permanently delete the user's account.", {
                            id: "offboarding.action.delete.description",
                        })}`,
                    },
                ]}
            ></ak-radio-input>

            <ak-form-element-horizontal name="scheduledAt" required>
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "offboarding-date-input",
                    },
                    msg("Scheduled for", { id: "offboarding.field.scheduled-for.label" }),
                )}
                <input
                    id="offboarding-date-input"
                    type="datetime-local"
                    data-type="datetime-local"
                    value=${dateTimeLocal(this.scheduledAt)}
                    min=${dateTimeLocal(this.scheduledMinimumDate)}
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg("The offboarding action runs at this time.", {
                        id: "offboarding.field.scheduled-for.description",
                    })}
                </p>
            </ak-form-element-horizontal>

            <ak-switch-input
                name="revokeSessions"
                label=${msg("Revoke sessions", { id: "offboarding.field.revoke-sessions.label" })}
                ?checked=${true}
                help=${msg("Revoke all of the user's sessions when offboarding.", {
                    id: "offboarding.field.revoke-sessions.description",
                })}
            ></ak-switch-input>

            <ak-switch-input
                name="revokeTokens"
                label=${msg("Revoke tokens", { id: "offboarding.field.revoke-tokens.label" })}
                ?checked=${true}
                help=${msg("Revoke all of the user's tokens when offboarding.", {
                    id: "offboarding.field.revoke-tokens.description",
                })}
            ></ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-offboarding-form": UserOffboardingForm;
    }
}
