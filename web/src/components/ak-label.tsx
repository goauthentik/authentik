import { FC } from "@goauthentik/lit-jsx/jsx-runtime";

import type { LabelHTMLAttributes } from "react";

import { nothing } from "lit";

export interface FormLabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
    required?: boolean;
    children?: string;
}

export const AKLabel: FC<FormLabelProps> = ({
    required,
    htmlFor,
    children,
    ...labelAttributes
} = {}) => {
    if (!children) return nothing;

    return (
        <label className="pf-c-form__label" htmlFor={htmlFor} {...labelAttributes}>
            <span className="pf-c-form__label-text">{children}</span>
            {required ? (
                <span className="pf-c-form__label-required" aria-hidden="true">
                    *
                </span>
            ) : null}
        </label>
    );
};
