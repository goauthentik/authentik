import { TemplateResult, html } from "lit-html";

export function formGroup(label: string, body: TemplateResult): TemplateResult {
    return html`<div class="pf-c-form__group">
            <div class="pf-c-form__group-label">
                <label class="pf-c-form__label">
                    <span class="pf-c-form__label-text">${label}</span>
                </label>
            </div>
            <div class="pf-c-form__group-control">
                <div class="pf-c-form__horizontal-group">
                    ${body}
                </div>
            </div>
        </div>`;
}
