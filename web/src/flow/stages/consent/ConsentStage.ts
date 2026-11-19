import "#flow/FormStatic";
import "#flow/components/ak-flow-card";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";
import PFText from "@patternfly/patternfly/utilities/Text/text.css";

import { SlottedTemplateResult } from "#elements/types";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import {
    ConsentChallenge,
    ConsentChallengeResponseRequest,
    ConsentPermission,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-consent")
export class ConsentStage extends BaseStage<ConsentChallenge, ConsentChallengeResponseRequest> {
    static styles: CSSResult[] = [
        PFLogin,
        PFList,
        PFForm,
        PFSpacing,
        PFFormControl,
        PFTitle,
        PFButton,
        PFText,
    ];

    renderPermissions(perms: ConsentPermission[]): TemplateResult {
        return html`${perms.map((permission) => {
            if (permission.name === "") {
                return nothing;
            }

            // Special case for openid Scope
            if (permission.id === "openid") {
                return nothing;
            }

            return html`<li data-permission-code="${permission.id}">${permission.name}</li>`;
        })}`;
    }

    /**
     * Name the OAuth client when it is not the application's own provider client.
     * Both fields are untrusted for dynamically registered clients; they are only
     * ever rendered as text.
     */
    renderClient(): SlottedTemplateResult {
        const { clientId, clientName, redirectHost } = this.challenge ?? {};

        if (!clientId) {
            return nothing;
        }

        const client = clientName || clientId;

        return html`<div class="pf-c-form__group" data-test-id="consent-client">
            <p class="pf-u-mb-sm pf-u-font-weight-bold">
                ${msg(str`${client} is requesting access on behalf of this application.`)}
            </p>
            ${
                clientName && clientName !== clientId
                    ? html`<p class="pf-u-mb-sm">${msg(str`Client ID: ${clientId}`)}</p>`
                    : nothing
            }
            ${
                redirectHost
                    ? html`<p class="pf-u-mb-sm">
                          ${msg(str`You will be redirected to ${redirectHost}.`)}
                      </p>`
                    : nothing
            }
        </div>`;
    }

    renderNoPrevious(): TemplateResult {
        return html`
            <div class="pf-c-form__group">
                <h3 data-test-id="stage-heading" class="pf-c-title pf-m-xl pf-u-mb-md">
                    ${this.challenge?.headerText ?? ""}
                </h3>
                ${this.renderClient()}
                ${
                    this.challenge?.permissions.length
                        ? html`
                              <p class="pf-u-mb-md">
                                  ${msg("Application requires following permissions:")}
                              </p>
                              <ul class="pf-c-list" id="permissions">
                                  ${this.renderPermissions(this.challenge.permissions)}
                              </ul>
                          `
                        : nothing
                }
            </div>
        `;
    }

    renderAdditional(): TemplateResult {
        return html`
            <div class="pf-c-form__group">
                <h3 data-test-id="stage-heading" class="pf-c-title pf-m-xl pf-u-mb-md">
                    ${this.challenge?.headerText ?? ""}
                </h3>
                ${this.renderClient()}
                ${
                    this.challenge?.permissions.length
                        ? html`
                              <p class="pf-u-mb-md">
                                  ${msg("Application already has access to the following permissions:")}
                              </p>
                              <ul class="pf-c-list" id="permissions">
                                  ${this.renderPermissions(this.challenge.permissions)}
                              </ul>
                          `
                        : nothing
                }
            </div>
            <div class="pf-c-form__group">
                ${
                    this.challenge?.additionalPermissions.length
                        ? html`
                              <p class="pf-u-font-weight-bold pf-u-mb-md">
                                  ${msg("Application requires following new permissions:")}
                              </p>
                              <ul class="pf-c-list" id="permissions">
                                  ${this.renderPermissions(this.challenge.additionalPermissions)}
                              </ul>
                          `
                        : nothing
                }
            </div>
        `;
    }

    protected render(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

        return html`<ak-flow-card .challenge=${this.challenge}>
            <form
                class="pf-c-form"
                @submit=${(event: SubmitEvent) => {
                    if (!this.challenge) {
                        return;
                    }

                    this.submitForm(event, {
                        token: this.challenge.token,
                    });
                }}
            >
                ${FlowUserDetails({ challenge: this.challenge })}
                ${
                    this.challenge?.additionalPermissions.length
                        ? this.renderAdditional()
                        : this.renderNoPrevious()
                }

                <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    <button
                        name="continue"
                        type="submit"
                        class="pf-c-button pf-m-primary pf-m-block"
                    >
                        ${msg("Continue")}
                    </button>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

export default ConsentStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-consent": ConsentStage;
    }
}
