import { msg } from "@lit/localize";
import { html } from "lit";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import { PromptTypeEnum, StagePrompt } from "@goauthentik/api";

import promptRenderers from "./FieldRenderers";

export function renderPromptInner(prompt: StagePrompt) {
    const renderer = promptRenderers.get(prompt.type);
    if (!renderer) {
        return html`<p>invalid type '${JSON.stringify(prompt.type, null, 2)}'</p>`;
    }
    return renderer(prompt);
}

export function renderPromptHelpText(prompt: StagePrompt) {
    if (prompt.subText === "") {
        return html``;
    }
    return html`<p class="pf-c-form__helper-text">${unsafeHTML(prompt.subText)}</p>`;
}

export function shouldRenderInWrapper(prompt: StagePrompt) {
    // Special types that aren't rendered in a wrapper
    const specialTypes = [PromptTypeEnum.Static, PromptTypeEnum.Hidden, PromptTypeEnum.Separator];
    const special = specialTypes.find((s) => s === prompt.type);
    return !special;
}

export function renderContinue() {
    return html` <div class="pf-c-form__group pf-m-action">
        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
            ${msg("Continue")}
        </button>
    </div>`;
}
