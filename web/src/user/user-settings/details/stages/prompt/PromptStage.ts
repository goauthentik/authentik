import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import { StagePrompt } from "@goauthentik/api";

import "../../../../../elements/forms/HorizontalFormElement";
import { PromptStage } from "../../../../../flows/stages/prompt/PromptStage";

@customElement("ak-user-stage-prompt")
export class UserSettingsPromptStage extends PromptStage {
    renderField(prompt: StagePrompt): TemplateResult {
        return html`
            <ak-form-element-horizontal
                label=${t`${prompt.label}`}
                ?required=${prompt.required}
                name=${prompt.fieldKey}
            >
                ${unsafeHTML(this.renderPromptInner(prompt))} ${prompt.subText}
                ${this.renderPromptHelpText(prompt)}
            </ak-form-element-horizontal>
        `;
    }
}
