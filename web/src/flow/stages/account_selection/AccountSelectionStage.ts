import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import type {
    AccountSelectionChallenge,
    AccountSelectionChallengeUser,
    AccountSelectionChallengeResponseRequest,
} from "@goauthentik/api";
import { AccountSelectionChallengeResponseActionEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

@customElement("ak-stage-account-selection")
export class AccountSelectionStage extends BaseStage<
    AccountSelectionChallenge,
    AccountSelectionChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        PFLogin,
        PFForm,
        PFSpacing,
        PFButton,
        PFTitle,
        css`
            .account-list {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }

            .account-button {
                align-items: center;
                display: grid;
                gap: 0.75rem;
                grid-template-columns: 2.25rem minmax(0, 1fr);
                min-height: 3.75rem;
                padding: 0.625rem 0.75rem;
                text-align: left;
                width: 100%;
            }

            .account-button img {
                border-radius: 50%;
                height: 2.25rem;
                width: 2.25rem;
            }

            .account-name,
            .account-meta {
                display: block;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .account-name {
                font-weight: 600;
            }

            .account-meta {
                color: var(--pf-global--Color--200);
                font-size: 0.875rem;
            }

            .account-button.pf-m-primary .account-meta {
                color: var(--pf-global--palette--white);
            }
        `,
    ];

    renderAccount(account: AccountSelectionChallengeUser): TemplateResult {
        const label = account.name || account.username || account.email;
        const secondary =
            account.email && account.email !== label ? account.email : account.username;
        return html`<button
            type="button"
            class="pf-c-button ${account.isHint ? "pf-m-primary" : "pf-m-secondary"} account-button"
            ?autofocus=${account.isHint}
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
                ${secondary ? html`<span class="account-meta">${secondary}</span>` : nothing}
            </span>
        </button>`;
    }

    render(): TemplateResult {
        const app = this.challenge?.applicationName || "";
        const accounts = this.challenge?.accounts ?? [];
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                <div class="pf-c-form__group">
                    <h3 data-test-id="stage-heading" class="pf-c-title pf-m-xl pf-u-mb-md">
                        ${msg("Continue as")}
                    </h3>
                    ${app
                        ? html`<p class="pf-u-mb-md">
                              ${msg(str`Select which account to use for ${app}.`)}
                          </p>`
                        : nothing}
                </div>

                <div class="pf-c-form__group account-list">
                    ${accounts.map((account) => this.renderAccount(account))}
                </div>

                <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    <button
                        type="button"
                        class="pf-c-button pf-m-link pf-m-block"
                        @click=${() =>
                            this.host.submit({
                                action: AccountSelectionChallengeResponseActionEnum.Login,
                            })}
                    >
                        ${msg("Use another account")}
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
