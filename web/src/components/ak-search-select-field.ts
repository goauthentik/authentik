import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/ak-search-select";
import type {
    SearchSelectActionEvent,
    SearchSelectChangeEvent,
} from "#elements/forms/SearchSelect/events";
import type { SearchSelectSource } from "#elements/forms/SearchSelect/shared";
import type { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { AKFormErrors, ErrorProp } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { html, nothing } from "lit";

export interface SearchSelectProps<T> {
    /**
     * The form field name.
     */
    name: string;
    source: SearchSelectSource<T>;
    id?: string;
    label?: string | null;
    placeholder?: string | null;
    /**
     * The key of the current object.
     */
    value?: string | null;
    /**
     * The current object, to label the field before the options load.
     */
    selectedObject?: T | null;
    required?: boolean;
    /**
     * Offer an empty option. Defaults to allowing it when the field is optional.
     */
    blankable?: boolean;
    emptyOption?: string | null;
    /**
     * What the field serializes as when nothing is chosen. Defaults to `null`.
     */
    emptyValue?: string | null;
    creatable?: boolean;
    readOnly?: boolean;
    actionLabel?: string | null;
    errors?: ErrorProp[] | readonly ErrorProp[] | null;
    onChange?: (event: SearchSelectChangeEvent<T>) => void;
    onAction?: (event: SearchSelectActionEvent) => void;
}

/**
 * A search select for one kind of API object, with its field errors.
 */
export function AKSearchSelect<T>({
    name,
    source,
    id,
    label,
    placeholder,
    value,
    selectedObject,
    required = false,
    blankable = !required,
    emptyOption,
    emptyValue = null,
    creatable = false,
    readOnly = false,
    actionLabel,
    errors,
    onChange,
    onAction,
}: SearchSelectProps<T>): SlottedTemplateResult {
    return html`<ak-search-select
            id=${ifPresent(id)}
            name=${name}
            .source=${source}
            .value=${value ?? ""}
            .selectedObject=${selectedObject ?? null}
            .emptyValue=${emptyValue}
            label=${ifPresent(label)}
            placeholder=${ifPresent(placeholder)}
            empty-option=${ifPresent(emptyOption)}
            action-label=${ifPresent(actionLabel)}
            ?required=${required}
            ?blankable=${blankable}
            ?creatable=${creatable}
            ?readonly=${readOnly}
            @ak-change=${onChange}
            @ak-search-select-action=${onAction}
        ></ak-search-select>
        ${AKFormErrors({ errors })}`;
}

export interface SearchSelectFieldProps<T> extends SearchSelectProps<T> {
    label: string;
    /**
     * Help text shown under the field.
     */
    help?: SlottedTemplateResult;
}

/**
 * A complete form field around a search select: its label, the select, and help text.
 */
export function AKSearchSelectField<T>({
    help,
    ...searchProps
}: SearchSelectFieldProps<T>): SlottedTemplateResult {
    const { name, label, required = false } = searchProps;
    const id = searchProps.id ?? name;

    return html`<ak-form-element-horizontal name=${name} ?required=${required}>
        ${AKLabel(
            {
                className: "pf-c-form__group-label",
                slot: "label",
                htmlFor: id,
                required,
            },
            label,
        )}
        ${AKSearchSelect({ ...searchProps, id })}
        ${help ? html`<p class="pf-c-form__helper-text">${help}</p>` : nothing}
    </ak-form-element-horizontal>`;
}
