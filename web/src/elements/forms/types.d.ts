/**
 * @file Type definitions for form-associated elements.
 *
 * While these types are part of the HTML standard, they're not yet defined
 * in the TypeScript standard library, so we define them here.
 *
 * @expires 2026-01-01
 */

/**
 * Callbacks for form-associated elements.
 */
interface HTMLElement {
    /**
     * A callback invoked when the browser autofilling sets a value.
     */
    formStateRestoreCallback?(state: FormValue, mode: "autocomplete"): void;
    /**
     * A callback invoked when the browser restores a value from a previous session.
     */
    formStateRestoreCallback?(state: FormValue, mode: "restore"): void;
    /**
     * A callback invoked when the browser restores a value from a previous session.
     */
    formStateRestoreCallback?(state: FormValue, mode: "restore" | "autocomplete"): void;

    /**
     * A callback that is invoked when the form is reset.
     */
    formResetCallback?(): void;

    /**
     * A callback that is invoked when the element's disabled state changes.
     */
    formDisabledCallback?(disabled: boolean): void;

    /**
     * A callback that is invoked when the element is associated with a form.
     */
    formAssociatedCallback?(form: HTMLFormElement): void;
}
