import "@goauthentik/elements/EmptyState";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

import { ConsentChallenge, ConsentChallengeResponseRequest, Permission } from "@goauthentik/api";

@customElement("ak-stage-consent")
export class ConsentStage extends BaseStage<ConsentChallenge, ConsentChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFList, PFForm, PFSpacing, PFFormControl, PFTitle, PFButton];
    }

    renderPermissions(perms: Permission[]): TemplateResult {
        return html`${perms.map((permission) => {
            if (permission.name === "") {
                return html``;
            }
            // Special case for openid Scope
            if (permission.id === "openid") {
                return html``;
            }
            return html`<li data-permission-code="${permission.id}">${permission.name}</li>`;
        })}`;
    }

    renderNoPrevious(): TemplateResult {
        return html`
            <div class="pf-c-form__group">
                <h3 id="header-text" class="pf-c-title pf-m-xl pf-u-mb-xl">
                    ${this.challenge.headerText}
                </h3>
                ${this.challenge.permissions.length > 0
                    ? html`
                          <p class="pf-u-mb-sm">
                              ${msg("Application requires following permissions:")}
                          </p>
                          <ul class="pf-c-list" id="permissions">
                              ${this.renderPermissions(this.challenge.permissions)}
                          </ul>
                      `
                    : html``}
            </div>
        `;
    }

    renderAdditional(): TemplateResult {
        return html`
            <div class="pf-c-form__group">
                <h3 id="header-text" class="pf-c-title pf-m-xl pf-u-mb-xl">
                    ${this.challenge.headerText}
                </h3>
                ${this.challenge.permissions.length > 0
                    ? html`
                          <p class="pf-u-mb-sm">
                              ${msg("Application already has access to the following permissions:")}
                          </p>
                          <ul class="pf-c-list" id="permissions">
                              ${this.renderPermissions(this.challenge.permissions)}
                          </ul>
                      `
                    : html``}
            </div>
            <div class="pf-c-form__group pf-u-mt-md">
                ${this.challenge.additionalPermissions.length > 0
                    ? html`
                          <strong class="pf-u-mb-sm">
                              ${msg("Application requires following new permissions:")}
                          </strong>
                          <ul class="pf-c-list" id="permissions">
                              ${this.renderPermissions(this.challenge.additionalPermissions)}
                          </ul>
                      `
                    : html``}
            </div>
        `;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e, {
                            token: this.challenge.token,
                        });
                    }}
                >
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}
                    >
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                                >${msg("Not you?")}</a
                            >
                        </div>
                    </ak-form-static>
                    ${this.challenge.additionalPermissions.length > 0
                        ? this.renderAdditional()
                        : this.renderNoPrevious()}

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${msg("Continue")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
