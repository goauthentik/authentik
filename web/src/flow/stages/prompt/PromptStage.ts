import "@goauthentik/elements/Divider";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCheck from "@patternfly/patternfly/components/Check/check.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    PromptChallenge,
    PromptChallengeResponseRequest,
    PromptTypeEnum,
    StagePrompt,
} from "@goauthentik/api";

import { renderCheckbox } from "./FieldRenderers";
import {
    renderContinue,
    renderPromptHelpText,
    renderPromptInner,
    shouldRenderInWrapper,
} from "./helpers";

@customElement("ak-stage-prompt")
export class PromptStage extends BaseStage<PromptChallenge, PromptChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFAlert,
            PFForm,
            PFFormControl,
            PFTitle,
            PFButton,
            PFCheck,
            css`
                textarea {
                    min-height: 4em;
                    max-height: 15em;
                    resize: vertical;
                }
            `,
        ];
    }

    /* TODO: Legacy: None of these refer to the `this` field. Static fields are a code smell. */

    renderPromptInner(prompt: StagePrompt) {
        return renderPromptInner(prompt);
    }
    renderPromptHelpText(prompt: StagePrompt) {
        return renderPromptHelpText(prompt);
    }
    shouldRenderInWrapper(prompt: StagePrompt) {
        return shouldRenderInWrapper(prompt);
    }

    renderField(prompt: StagePrompt): TemplateResult {
        // Checkbox has a slightly different layout, so it must be intercepted early.
        if (prompt.type === PromptTypeEnum.Checkbox) {
            return renderCheckbox(prompt);
        }

        if (shouldRenderInWrapper(prompt)) {
            return html`<ak-form-element
                label="${prompt.label}"
                ?required="${prompt.required}"
                class="pf-c-form__group"
                .errors=${(this.challenge?.responseErrors || {})[prompt.fieldKey]}
            >
                ${renderPromptInner(prompt)} ${renderPromptHelpText(prompt)}
            </ak-form-element>`;
        }
        return html` ${renderPromptInner(prompt)} ${renderPromptHelpText(prompt)}`;
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
                        this.submitForm(e);
                    }}
                >
                    ${this.challenge.fields.map((prompt) => {
                        return this.renderField(prompt);
                    })}
                    ${"non_field_errors" in (this.challenge?.responseErrors || {})
                        ? this.renderNonFieldErrors(
                              this.challenge?.responseErrors?.non_field_errors || [],
                          )
                        : html``}
                    ${renderContinue()}
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
