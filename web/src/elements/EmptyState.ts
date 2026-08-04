/**
 * @file Barrel file and default registry ('ak-empty-state') for the EmptyState component
 */

import {
    akEmptyState,
    EmptyState,
    type EmptyStateContentProps,
    type EmptyStateProps,
} from "./EmptyState_impl/EmptyState";

export { akEmptyState, EmptyState };
export type { EmptyStateContentProps, EmptyStateProps };

window.customElements.define("ak-empty-state", EmptyState);

declare global {
    interface HTMLElementTagNameMap {
        "ak-empty-state": EmptyState;
    }
}
