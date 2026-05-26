import "#flow/components/ak-flow-card";

import { docLink } from "#common/global";

import { BaseStage } from "#flow/stages/base";

import type {
    AccountSelectionChallenge,
    AccountSelectionChallengeResponseRequest,
    AccountSelectionChallengeUser,
} from "@goauthentik/api";
import { AccountSelectionChallengeResponseActionEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";

@customElement("ak-stage-account-selection")
export class AccountSelectionStage extends BaseStage<
    AccountSelectionChallenge,
    AccountSelectionChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        PFLogin,
        PFForm,
        PFButton,
        css`
            .account-list {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }

            .account-selection-help {
                color: var(--pf-global--Color--200);
                font-size: var(--pf-global--FontSize--sm);
                line-height: 1.4;
                margin-block: 0;
            }

            .account-selection-help a {
                margin-inline-start: 0.25rem;
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

            .account-button-hint {
                box-shadow: inset 0.25rem 0 0 var(--pf-global--primary-color--100);
            }

            .account-button-hint .account-name {
                color: var(--pf-global--primary-color--100);
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
        `,
    ];

    renderAccount(account: AccountSelectionChallengeUser): TemplateResult {
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
                ${secondary ? html`<span class="account-meta">${secondary}</span>` : nothing}
            </span>
        </button>`;
    }

    render(): TemplateResult {
        const accounts = this.challenge?.accounts ?? [];
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                <div class="pf-c-form__group">
                    <p class="account-selection-help">
                        ${msg("Choose which signed-in account authentik should use for this flow.")}
                        <a
                            href=${docLink(
                                "/add-secure-apps/flows-stages/stages/account_selection/",
                            )}
                            target="_blank"
                            rel="noopener noreferrer"
                            >${msg("Learn more")}</a
                        >
                    </p>
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
