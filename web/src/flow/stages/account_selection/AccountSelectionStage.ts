import "#flow/components/ak-flow-card";

import { docLink } from "#common/global";

import Styles from "#flow/stages/account_selection/AccountSelectionStage.css";
import { BaseStage } from "#flow/stages/base";

import type {
    AccountSelectionChallenge,
    AccountSelectionChallengeResponseRequest,
    AccountSelectionChallengeUser,
} from "@goauthentik/api";
import { AccountSelectionChallengeResponseActionEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";

@customElement("ak-stage-account-selection")
export class AccountSelectionStage extends BaseStage<
    AccountSelectionChallenge,
    AccountSelectionChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFButton, Styles];

    protected dispatchAccountSelectionSubmit = (): void => {
        this.host.submit({
            action: AccountSelectionChallengeResponseActionEnum.Login,
        });
    };

    protected renderAccount(account: AccountSelectionChallengeUser): TemplateResult {
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
                    action: account.isCurrent
                        ? AccountSelectionChallengeResponseActionEnum.Continue
                        : AccountSelectionChallengeResponseActionEnum.Switch,
                    selectedAccount: account.uid,
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
                    <p class="account-selection-help">
                        ${msg(
                            "Choose which signed-in account authentik should use for this flow.",
                            {
                                id: "account-selection.help.description",
                            },
                        )}
                        <a
                            href=${docLink(
                                "/add-secure-apps/flows-stages/stages/account_selection/",
                            )}
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
                            id: "account-selection.form-actions.legend",
                        })}
                    </legend>
                    <button
                        type="button"
                        class="pf-c-button pf-m-link pf-m-block"
                        @click=${this.dispatchAccountSelectionSubmit}
                    >
                        ${msg("Use another account", {
                            id: "account-selection.actions.use-another-account.label",
                        })}
                    </button>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

export default AccountSelectionStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-account-selection": AccountSelectionStage;
    }
}
