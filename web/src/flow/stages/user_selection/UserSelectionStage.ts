import "#flow/components/ak-flow-card";

import { docLink } from "#common/global";

import { BaseStage } from "#flow/stages/base";
import Styles from "#flow/stages/user_selection/UserSelectionStage.css";

import type {
    UserSelectionChallenge,
    UserSelectionChallengeResponseRequest,
    UserSelectionChallengeUser,
} from "@goauthentik/api";
import { UserSelectionChallengeResponseActionEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";

@customElement("ak-stage-user-selection")
export class UserSelectionStage extends BaseStage<
    UserSelectionChallenge,
    UserSelectionChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFButton, Styles];

    protected dispatchUserSelectionSubmit = (): void => {
        this.host.submit({
            action: UserSelectionChallengeResponseActionEnum.Login,
        });
    };

    protected renderAccount(account: UserSelectionChallengeUser): TemplateResult {
        const label = account.name || account.username || account.email;
        const secondary =
            account.email && account.email !== label ? account.email : account.username;
        return html`<button
            type="button"
            class="pf-c-button pf-m-secondary account-button ${account.isHint
                ? "account-button-hint"
                : ""}"
            @click=${() =>
                this.host.submit({
                    action: UserSelectionChallengeResponseActionEnum.Continue,
                    selectedUser: account.uid,
                })}
        >
            <img src=${account.avatar} alt="" />
            <span>
                <span class="account-name">${label}</span>
                ${secondary ? html`<span class="account-meta">${secondary}</span>` : null}
            </span>
        </button>`;
    }

    render(): TemplateResult {
        const accounts = this.challenge?.accounts ?? [];
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                <div class="pf-c-form__group">
                    <p class="user-selection-help">
                        ${msg("Choose which account authentik should use for this flow.", {
                            id: "user-selection.help.description",
                        })}
                        <a
                            href=${docLink("/add-secure-apps/flows-stages/stages/user_selection/")}
                            target="_blank"
                            rel="noopener noreferrer"
                            >${msg("Learn more", {
                                id: "common.actions.learn-more.label",
                            })}</a
                        >
                    </p>
                </div>

                <div class="pf-c-form__group account-list">
                    ${accounts.map((account) => this.renderAccount(account))}
                </div>

                <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
                    <legend class="sr-only">
                        ${msg("Form actions", {
                            id: "user-selection.form-actions.legend",
                        })}
                    </legend>
                    <button
                        type="button"
                        class="pf-c-button pf-m-link pf-m-block"
                        @click=${this.dispatchUserSelectionSubmit}
                    >
                        ${msg("Use another account", {
                            id: "user-selection.actions.use-another-account.label",
                        })}
                    </button>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

export default UserSelectionStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-user-selection": UserSelectionStage;
    }
}
