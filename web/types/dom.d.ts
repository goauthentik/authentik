/**
 * @file Global DOM-related types.
 */

export {};

declare global {
    /**
     * The possible values for the `closedBy` property of {@linkcode HTMLDialogElement}.
     */
    type ClosedBy = "any" | "closerequest" | "none";

    interface HTMLDialogElement {
        /**
         * Indicates the types of user actions that can be used to close the associated <dialog> element.
         *
         * @attr closedby
         * @see {@link https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/closedBy MDN}
         */
        closedBy: ClosedBy;
    }
}
