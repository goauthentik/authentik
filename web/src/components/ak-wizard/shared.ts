import { SlottedTemplateResult } from "#elements/types";

import { msg, str } from "@lit/localize";
import { html } from "lit-html";

export type WizardButton =
    | { kind: "back"; label?: string; destination: string }
    | { kind: "cancel"; label?: string }
    | { kind: "close"; label?: string }
    | { kind: "next"; label?: string; destination: string }
    | { kind: "create"; label?: string; destination: string }
    | { kind: "finish"; label?: string; destination: string };

export const DialogDismissalKinds: ReadonlySet<ButtonKind> = new Set(["close", "cancel", "finish"]);

export type NavigableButton = Extract<WizardButton, { destination: string }>;

export type ButtonKind = Extract<WizardButton["kind"], PropertyKey>;

declare const labelFactoryBrand: unique symbol;

// Branded so a forgotten `()` at a call site — e.g. `return record.close;` in a
// `SlottedTemplateResult`-returning method — is rejected by `tsc` instead of
// rendering as visible noise in the live UI (see goauthentik/authentik#22222).
export type LabelFactory = ((verboseName?: string) => SlottedTemplateResult) & {
    readonly [labelFactoryBrand]: true;
};

const labelFactory = (fn: (verboseName?: string) => SlottedTemplateResult): LabelFactory =>
    fn as LabelFactory;

export interface WizardStepLabel {
    label: string;
    id: string;
    enabled?: boolean;
}

export type WizardStepState = {
    currentStep: string | null;
    stepLabels: WizardStepLabel[];
};

export const isNavigable = (b: WizardButton): b is NavigableButton =>
    "destination" in b && typeof b.destination === "string" && b.destination.length > 0;

export const ButtonKindClassnameRecord = {
    next: "pf-m-primary",
    create: "pf-m-primary",
    finish: "pf-m-primary",
    back: "pf-m-secondary",
    close: "pf-m-link",
    cancel: "pf-m-plain",
} as const satisfies Record<ButtonKind, string>;

export const ButtonKindLabelRecord = {
    next: labelFactory(() => {
        return html`${msg("Next")}
            <span class="pf-c-button__icon pf-m-end">
                <i class="fas fa-arrow-right" aria-hidden="true"></i>
            </span>`;
    }),
    create: labelFactory((verboseName?: string) => {
        const label = verboseName
            ? msg(str`Create ${verboseName}`, {
                  id: "form.create-submit",
              })
            : msg("Create", {
                  id: "form.create-submit-no-entity",
              });

        return html`${label}
            <span class="pf-c-button__icon pf-m-end">
                <i class="fas fa-check" aria-hidden="true"></i>
            </span>`;
    }),
    finish: labelFactory(() => {
        return html`${msg("Finish")}
            <span class="pf-c-button__icon pf-m-end">
                <i class="fas fa-check" aria-hidden="true"></i>
            </span>`;
    }),
    back: labelFactory(() => {
        return html`<span class="pf-c-button__icon pf-m-start">
                <i class="fas fa-arrow-left" aria-hidden="true"></i>
            </span>
            ${msg("Back")}`;
    }),

    cancel: labelFactory(() => msg("Cancel")),
    close: labelFactory(() => msg("Close")),
} as const satisfies Record<ButtonKind, LabelFactory>;
