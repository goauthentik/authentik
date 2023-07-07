import { TemplateResult, html } from "lit";

import "@patternfly/patternfly/components/Alert/alert.css";
import "@patternfly/patternfly/components/Button/button.css";
import "@patternfly/patternfly/components/Check/check.css";
import "@patternfly/patternfly/components/Form/form.css";
import "@patternfly/patternfly/components/FormControl/form-control.css";
import "@patternfly/patternfly/components/Login/login.css";
import "@patternfly/patternfly/components/Title/title.css";
import "@patternfly/patternfly/patternfly-base.css";

import { PromptTypeEnum } from "@goauthentik/api";
import type { StagePrompt } from "@goauthentik/api";

import promptRenderers from "./FieldRenderers";
import { renderContinue, renderPromptHelpText, renderPromptInner } from "./helpers";

// Storybook stories are meant to show not just that the objects work, but to document good
// practices around using them.  Because of their uniform signature, the renderers can easily
// be encapsulated into containers that show them at their most functional, even without
// building Shadow DOMs with which to do it.  This is 100% Light DOM work, and they still
// work well.

const baseRenderer = (prompt: TemplateResult) =>
    html`<div style="background: #fff; padding: 4em; max-width: 24em;">
        <style>
            input,
            textarea,
            select,
            button,
            .pf-c-form__helper-text:not(.pf-m-error),
            input + label.pf-c-check__label {
                color: #000;
            }
            input[readonly],
            textarea[readonly] {
                color: #fff;
            }
        </style>
        ${prompt}
    </div>`;

function renderer(kind: PromptTypeEnum, prompt: Partial<StagePrompt>) {
    const renderer = promptRenderers.get(kind);
    if (!renderer) {
        throw new Error(`A renderer of type ${kind} does not exist.`);
    }
    return baseRenderer(html`${renderer(prompt as StagePrompt)}`);
}

const textPrompt = {
    fieldKey: "test_text_field",
    placeholder: "This is the placeholder",
    required: false,
    initialValue: "initial value",
};

export const Text = () => renderer(PromptTypeEnum.Text, textPrompt);
export const TextArea = () => renderer(PromptTypeEnum.TextArea, textPrompt);
export const TextReadOnly = () => renderer(PromptTypeEnum.TextReadOnly, textPrompt);
export const TextAreaReadOnly = () => renderer(PromptTypeEnum.TextAreaReadOnly, textPrompt);
export const Username = () => renderer(PromptTypeEnum.Username, textPrompt);
export const Password = () => renderer(PromptTypeEnum.Password, textPrompt);

const emailPrompt = { ...textPrompt, initialValue: "example@example.fun" };
export const Email = () => renderer(PromptTypeEnum.Email, emailPrompt);

const numberPrompt = { ...textPrompt, initialValue: "10" };
export const Number = () => renderer(PromptTypeEnum.Number, numberPrompt);

const datePrompt = { ...textPrompt, initialValue: "2018-06-12T19:30" };
export const Date = () => renderer(PromptTypeEnum.Date, datePrompt);
export const DateTime = () => renderer(PromptTypeEnum.DateTime, datePrompt);

const separatorPrompt = { placeholder: "😊" };
export const Separator = () => renderer(PromptTypeEnum.Separator, separatorPrompt);

const staticPrompt = { initialValue: "😊" };
export const Static = () => renderer(PromptTypeEnum.Static, staticPrompt);

const choicePrompt = {
    fieldKey: "test_text_field",
    placeholder: "This is the placeholder",
    required: false,
    initialValue: "first",
    choices: ["first", "second", "third"],
};

export const Dropdown = () => renderer(PromptTypeEnum.Dropdown, choicePrompt);
export const RadioButtonGroup = () => renderer(PromptTypeEnum.RadioButtonGroup, choicePrompt);

const checkPrompt = { ...textPrompt, label: "Favorite Subtext?", subText: "(Xena & Gabrielle)" };
export const Checkbox = () => renderer(PromptTypeEnum.Checkbox, checkPrompt);

const localePrompt = { ...textPrompt, initialValue: "en" };
export const Locale = () => renderer(PromptTypeEnum.AkLocale, localePrompt);

export const PromptFailure = () =>
    baseRenderer(renderPromptInner({ type: null } as unknown as StagePrompt));

export const HelpText = () =>
    baseRenderer(renderPromptHelpText({ subText: "There is no subtext here." } as StagePrompt));

export const Continue = () => baseRenderer(renderContinue());

export default {
    title: "Flow Components/Field Renderers",
};
