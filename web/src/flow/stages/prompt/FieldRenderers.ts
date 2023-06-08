import { LOCALES } from "@goauthentik/common/ui/locale";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/password-match-indicator";
import "@goauthentik/elements/password-strength-indicator";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import { CapabilitiesEnum, PromptTypeEnum, StagePrompt } from "@goauthentik/api";

export function password(prompt: StagePrompt) {
    return html`<input
            type="password"
            name="${prompt.fieldKey}"
            placeholder="${prompt.placeholder}"
            autocomplete="new-password"
            class="pf-c-form-control"
            ?required=${prompt.required}
        /><ak-password-strength-indicator
            src='input[name="${prompt.fieldKey}"]'
        ></ak-password-strength-indicator>`;
}

const REPEAT = /_repeat/;

export function repeatPassword(prompt: StagePrompt) {
    const first = `input[name="${prompt.fieldKey}"]`;
    const second = `input[name="${prompt.fieldKey.replace(REPEAT, "")}"]`;

    return html` <div style="display:flex; flex-direction:row; gap: 0.5em; align-content: center">
        <input
            style="flex:1 0"
            type="password"
            name="${prompt.fieldKey}"
            placeholder="${prompt.placeholder}"
            autocomplete="new-password"
            class="pf-c-form-control"
            ?required=${prompt.required}
        /><ak-password-match-indicator
            first="${first}"
            second="${second}"
        ></ak-password-match-indicator>
    </div>`;
}

export function renderPassword(prompt: StagePrompt) {
    return REPEAT.test(prompt.fieldKey) ? repeatPassword(prompt) : password(prompt);
}

export function renderText(prompt: StagePrompt) {
    return html`<input
        type="text"
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        autocomplete="off"
        class="pf-c-form-control"
        ?required=${prompt.required}
        value="${prompt.initialValue}"
    />`;
}

export function renderTextArea(prompt: StagePrompt) {
    return html`<textarea
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        autocomplete="off"
        class="pf-c-form-control"
        ?required=${prompt.required}
    >
${prompt.initialValue}</textarea
    >`;
}

export function renderTextReadOnly(prompt: StagePrompt) {
    return html`<input
        type="text"
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        class="pf-c-form-control"
        ?readonly=${true}
        value="${prompt.initialValue}"
    />`;
}

export function renderTextAreaReadOnly(prompt: StagePrompt) {
    return html`<textarea
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        class="pf-c-form-control"
        readonly
    >
${prompt.initialValue}</textarea
    >`;
}

export function renderUsername(prompt: StagePrompt) {
    return html`<input
        type="text"
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        autocomplete="username"
        class="pf-c-form-control"
        ?required=${prompt.required}
        value="${prompt.initialValue}"
    />`;
}

export function renderEmail(prompt: StagePrompt) {
    return html`<input
        type="email"
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        class="pf-c-form-control"
        ?required=${prompt.required}
        value="${prompt.initialValue}"
    />`;
}

export function renderNumber(prompt: StagePrompt) {
    return html`<input
        type="number"
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        class="pf-c-form-control"
        ?required=${prompt.required}
        value="${prompt.initialValue}"
    />`;
}

export function renderDate(prompt: StagePrompt) {
    return html`<input
        type="date"
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        class="pf-c-form-control"
        ?required=${prompt.required}
        value="${prompt.initialValue}"
    />`;
}

export function renderDateTime(prompt: StagePrompt) {
    return html`<input
        type="datetime"
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        class="pf-c-form-control"
        ?required=${prompt.required}
        value="${prompt.initialValue}"
    />`;
}

export function renderFile(prompt: StagePrompt) {
    return html`<input
        type="file"
        name="${prompt.fieldKey}"
        placeholder="${prompt.placeholder}"
        class="pf-c-form-control"
        ?required=${prompt.required}
        value="${prompt.initialValue}"
    />`;
}

export function renderSeparator(prompt: StagePrompt) {
    return html`<ak-divider>${prompt.placeholder}</ak-divider>`;
}

export function renderHidden(prompt: StagePrompt) {
    return html`<input
        type="hidden"
        name="${prompt.fieldKey}"
        value="${prompt.initialValue}"
        class="pf-c-form-control"
        ?required=${prompt.required}
    />`;
}

export function renderStatic(prompt: StagePrompt) {
    return html`<p>${unsafeHTML(prompt.initialValue)}</p>`;
}

export function renderDropdown(prompt: StagePrompt) {
    return html`<select class="pf-c-form-control" name="${prompt.fieldKey}">
        ${prompt.choices?.map((choice) => {
            return html`<option value="${choice}" ?selected=${prompt.initialValue === choice}>
                ${choice}
            </option>`;
        })}
    </select>`;
}

export function renderRadioButtonGroup(prompt: StagePrompt) {
    return html`${(prompt.choices || []).map((choice) => {
        const id = `${prompt.fieldKey}-${choice}`;
        return html`<div class="pf-c-check">
            <input
                type="radio"
                class="pf-c-check__input"
                name="${prompt.fieldKey}"
                id="${id}"
                ?checked="${prompt.initialValue === choice}"
                ?required="${prompt.required}"
                value="${choice}"
            />
            <label class="pf-c-check__label" for=${id}>${choice}</label>
        </div> `;
    })}`;
}

export function renderAkLocale(prompt: StagePrompt) {
    // TODO: External reference.
    const inDebug = rootInterface()?.config?.capabilities.includes(CapabilitiesEnum.CanDebug);
    const locales = inDebug ? LOCALES : LOCALES.filter((locale) => locale.code !== "debug");
    const options = locales.map(
        (locale) => html`<option
            value=${locale.code}
            ?selected=${locale.code === prompt.initialValue}
        >
            ${locale.code.toUpperCase()} - ${locale.label()}
        </option> `,
    );

    return html`<select class="pf-c-form-control" name="${prompt.fieldKey}">
        <option value="" ?selected=${prompt.initialValue === ""}>
            ${msg("Auto-detect (based on your browser)")}
        </option>
        ${options}
    </select>`;
}

type Renderer = (prompt: StagePrompt) => TemplateResult;

export const promptRenderers = new Map<PromptTypeEnum, Renderer>([
    [PromptTypeEnum.Text, renderText],
    [PromptTypeEnum.TextArea, renderTextArea],
    [PromptTypeEnum.TextReadOnly, renderTextReadOnly],
    [PromptTypeEnum.TextAreaReadOnly, renderTextAreaReadOnly],
    [PromptTypeEnum.Username, renderUsername],
    [PromptTypeEnum.Email, renderEmail],
    [PromptTypeEnum.Password, renderPassword],
    [PromptTypeEnum.Number, renderNumber],
    [PromptTypeEnum.Date, renderDate],
    [PromptTypeEnum.DateTime, renderDateTime],
    [PromptTypeEnum.File, renderFile],
    [PromptTypeEnum.Separator, renderSeparator],
    [PromptTypeEnum.Hidden, renderHidden],
    [PromptTypeEnum.Static, renderStatic],
    [PromptTypeEnum.Dropdown, renderDropdown],
    [PromptTypeEnum.RadioButtonGroup, renderRadioButtonGroup],
    [PromptTypeEnum.AkLocale, renderAkLocale],
]);

export default promptRenderers;
