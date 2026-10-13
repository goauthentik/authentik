/**
 * @file Helpers for waiting on form fields whose value is not final yet.
 *   Kept free of DOM and Lit imports so the logic can be unit tested in Node.
 */

/**
 * A form field whose value may not be final yet, e.g. one that still has to load its options
 * before it can resolve a preselected value.
 */
export interface SettlingFormField {
    /**
     * Resolves once the field's value is final and safe to validate and serialize.
     */
    readonly settled: Promise<void>;
}

export function isSettlingFormField(element: object): element is SettlingFormField {
    return "settled" in element && element.settled instanceof Promise;
}

/**
 * How long {@linkcode settleFormFields} waits before giving up on a field, in milliseconds.
 */
export const FORM_FIELD_SETTLE_TIMEOUT = 10_000;

/**
 * Wait until every settling field associated with the given form has a final value.
 *
 * Never rejects, and resolves after `timeout` even if a field is still pending, e.g. because
 * its request failed or stalled. The caller's validation then reports the unfinished field
 * instead of the form hanging.
 */
export function settleFormFields(
    form: HTMLFormElement,
    timeout = FORM_FIELD_SETTLE_TIMEOUT,
): Promise<void> {
    const pending = Array.from(form.elements, (element) =>
        isSettlingFormField(element) ? element.settled : null,
    ).filter((settled) => settled !== null);

    if (!pending.length) return Promise.resolve();

    let timer: ReturnType<typeof setTimeout> | undefined;

    const deadline = new Promise<void>((resolve) => {
        timer = setTimeout(resolve, timeout);
    });

    return Promise.race([Promise.allSettled(pending), deadline]).then(() => {
        clearTimeout(timer);
    });
}
