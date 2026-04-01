import { dateToUTC } from "#common/temporal";

import { AKElement } from "#elements/Base";
import { isControlElement } from "#elements/ControlElement";
import { isNamedElement, NamedElement } from "#elements/utils/inputs";

function isIgnored<T extends Element>(element: T) {
    if (!(element instanceof HTMLElement)) return false;

    return element.dataset.formIgnore === "true";
}

/**
 * Recursively assign `value` into `json` while interpreting the dot-path of `element.name`
 */
function assignValue(
    element: NamedElement,
    value: unknown,
    destination: Record<string, unknown>,
): void {
    let parent = destination;

    if (!element.name?.includes(".")) {
        parent[element.name] = value;
        return;
    }

    const nameElements = element.name.split(".");

    for (let index = 0; index < nameElements.length - 1; index++) {
        const nameEl = nameElements[index];
        // Ensure all nested structures exist
        if (!(nameEl in parent)) {
            parent[nameEl] = {};
        }
        parent = parent[nameEl] as { [key: string]: unknown };
    }

    parent[nameElements[nameElements.length - 1]] = value;
}

/**
 * Convert the elements of the form to JSON.
 *
 */
export function serializeForm<T = Record<string, unknown>>(elements: Iterable<AKElement>): T {
    const json: Record<string, unknown> = {};

    Array.from(elements).forEach((element) => {
        element.requestUpdate();

        if (element.hidden) return;

        if (isNamedElement(element) && isControlElement(element)) {
            return assignValue(element, element.toJSON(), json);
        }

        const inputElement = element.querySelector("[name]");

        if (element.hidden || !inputElement || isIgnored(inputElement)) {
            return;
        }

        if (isNamedElement(element) && isControlElement(inputElement)) {
            return assignValue(element, inputElement.toJSON(), json);
        }

        if (inputElement instanceof HTMLSelectElement && inputElement.multiple) {
            const selectElement = inputElement as unknown as HTMLSelectElement;

            return assignValue(
                inputElement,
                Array.from(selectElement.selectedOptions, (v) => v.value),
                json,
            );
        }

        if (inputElement instanceof HTMLInputElement) {
            if (inputElement.type === "date") {
                return assignValue(inputElement, inputElement.valueAsDate, json);
            }

            if (inputElement.type === "datetime-local") {
                const valueAsNumber = inputElement.valueAsNumber;
                return assignValue(
                    inputElement,
                    isNaN(valueAsNumber) ? undefined : dateToUTC(new Date(valueAsNumber)),
                    json,
                );
            }

            if ("type" in inputElement.dataset && inputElement.dataset.type === "datetime-local") {
                // Workaround for Firefox <93, since 92 and older don't support
                // datetime-local fields
                const date = new Date(inputElement.value);
                return assignValue(
                    inputElement,
                    isNaN(date.getTime()) ? undefined : dateToUTC(date),
                    json,
                );
            }

            if (inputElement.type === "checkbox") {
                return assignValue(inputElement, inputElement.checked, json);
            }
        }

        if (isNamedElement(inputElement) && "value" in inputElement) {
            return assignValue(inputElement, inputElement.value, json);
        }

        console.error(`authentik/forms: Could not find value for element`, {
            element,
            inputElement,
            json,
        });

        throw new Error(`Could not find value for element ${inputElement.tagName}`);
    });

    return json as unknown as T;
}
