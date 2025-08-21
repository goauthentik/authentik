import { pluckErrorDetail } from "#common/errors/network";

import { LitFC } from "#elements/types";

import { ErrorDetail, ValidationError } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";

/**
 * An error originating from a form field.
 */
export type FieldErrorTuple = [fieldName: string, detail: string];

export type ErrorProp = string | Error | ErrorDetail | ValidationError | FieldErrorTuple;

export interface AKFormErrorsProps {
    errors?: ErrorProp[];
}

function renderError(detail: string) {
    if (!detail) {
        return nothing;
    }

    return html`<p class="pf-c-form__helper-text pf-m-error" aria-live="polite">
        <span class="pf-c-form__helper-text-icon">
            <i class="fas fa-exclamation-circle" aria-hidden="true"></i> </span
        >${detail}
    </p>`;
}

export const AKFormErrors: LitFC<AKFormErrorsProps> = ({ errors } = {}) => {
    if (!errors?.length) return nothing;

    return errors.flatMap((error) => {
        if (Array.isArray(error) && error.length === 2) {
            const [fieldName, detail] = error;

            return renderError(msg(str`${fieldName}: ${detail}`));
        }

        return renderError(pluckErrorDetail(error));
    });
};
