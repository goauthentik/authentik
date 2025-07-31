import { ErrorDetail } from "@goauthentik/api";

import { nothing } from "lit";

export interface AKFormErrorsProps {
    errors?: ErrorDetail[];
}

export const AKFormErrors: LitJSX.FC<AKFormErrorsProps> = ({ errors } = {}) => {
    if (!errors?.length) return nothing;

    return errors.map((error) => {
        return (
            <p className="pf-c-form__helper-text pf-m-error">
                <span className="pf-c-form__helper-text-icon">
                    <i className="fas fa-exclamation-circle" aria-hidden="true"></i>
                </span>
                {error.string}
            </p>
        );
    });
};
