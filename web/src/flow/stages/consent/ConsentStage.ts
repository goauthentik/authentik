import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import {
    ConsentChallenge,
    ConsentChallengeResponseRequest,
    ConsentPermission,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";
import PFText from "@patternfly/patternfly/utilities/Text/text.css";

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

    renderNoPrevious(): TemplateResult {
        return html`
            <div class="pf-c-form__group">
                <h3 data-test-id="stage-heading" class="pf-c-title pf-m-xl pf-u-mb-md">
                    ${this.challenge.headerText}
                </h3>
                ${this.challenge.permissions.length > 0
                    ? html`
                          <p class="pf-u-mb-md">
                              ${msg("Application requires following permissions:")}
                          </p>
                          <ul class="pf-c-list" id="permissions">
                              ${this.renderPermissions(this.challenge.permissions)}
                          </ul>
                      `
                    : nothing}
            </div>
        `;
    }

    renderAdditional(): TemplateResult {
        return html`
            <div class="pf-c-form__group">
                <h3 data-test-id="stage-heading" class="pf-c-title pf-m-xl pf-u-mb-md">
                    ${this.challenge.headerText}
                </h3>
                ${this.challenge.permissions.length > 0
                    ? html`
                          <p class="pf-u-mb-md">
                              ${msg("Application already has access to the following permissions:")}
                          </p>
                          <ul class="pf-c-list" id="permissions">
                              ${this.renderPermissions(this.challenge.permissions)}
                          </ul>
                      `
                    : nothing}
            </div>
            <div class="pf-c-form__group">
                ${this.challenge.additionalPermissions.length > 0
                    ? html`
                          <p class="pf-u-font-weight-bold pf-u-mb-md">
                              ${msg("Application requires following new permissions:")}
                          </p>
                          <ul class="pf-c-list" id="permissions">
                              ${this.renderPermissions(this.challenge.additionalPermissions)}
                          </ul>
                      `
                    : nothing}
            </div>
        `;
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form
                class="pf-c-form"
                @submit=${(event: SubmitEvent) => {
                    this.submitForm(event, {
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

                <fieldset class="pf-c-form__group pf-m-action">
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-consent": ConsentStage;
    }
}
