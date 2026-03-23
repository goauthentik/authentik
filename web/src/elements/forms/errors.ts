import { HorizontalFormElement } from "#elements/forms/HorizontalFormElement";

import { ErrorProp } from "#components/ak-field-errors";

import { ValidationError } from "@goauthentik/api";

import { snakeCase } from "change-case";

//#region Validation Reporting

/**
 * Assign all input-related errors to their respective elements.
 */
export function reportInvalidFields(
    parsedError: ValidationError,
    elements: Iterable<HorizontalFormElement>,
): HorizontalFormElement[] {
    const invalidFields: HorizontalFormElement[] = [];

    for (const element of elements) {
        element.requestUpdate();

        const elementName = element.name;

        if (!elementName) continue;

        const snakeProperty = snakeCase(elementName);
        const errorMessages: ErrorProp[] = parsedError[snakeProperty] ?? [];

        element.errorMessages = errorMessages;

        if (Array.isArray(errorMessages) && errorMessages.length) {
            invalidFields.push(element);
        }
    }

    return invalidFields;
}

//#endregion
