/**
 * @file Lit-specific globals applied to the Window object.
 */

export {};

declare global {
    interface HTMLElement {
        /**
         * A property defined by Lit to track the element part.
         */
        _$litPart$?: unknown;
    }

    interface Window {
        /**
         * A possible nonce to use create a CSP-safe style element.
         */
        litNonce?: string;
    }
}
