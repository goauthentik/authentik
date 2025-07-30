import { LitFC } from "#elements/types";

import { ErrorDetail } from "@goauthentik/api";

import { html, nothing } from "lit";

export interface AKFormErrorsProps {
    errors?: ErrorDetail[];
}

export const AKFormErrors: LitFC<AKFormErrorsProps> = ({ errors } = {}) => {
    if (!errors?.length) return nothing;

    return errors.map((error) => {
        return html`<p class="pf-c-form__helper-text pf-m-error">
            <span class="pf-c-form__helper-text-icon">
                <i class="fas fa-exclamation-circle" aria-hidden="true"></i> </span
            >${error.string}
        </p>`;
    });
};
