import { createMixin } from "#elements/types";

import { state } from "lit/decorators.js";

/**
 * A mixin that lazily renders the contents of `<ak-tabs>` panels.
 *
 * @see {@linkcode WithLazyTabs}
 */
export interface LazyTabsMixin {
    /**
     * The slot names of the tabs that have been activated at least once.
     *
     * Override the initial value to pre-activate a tab (e.g. the default one)
     * so its content renders on first paint.
     */
    activatedTabs: Set<string>;

    /**
     * Mark a tab as activated so its content renders and stays rendered.
     *
     * Wire this to each tab panel's `@activate` event.
     */
    activateTab(tab: string): void;

    /**
     * Render `content` once `tab` has been activated, otherwise `null`.
     */
    renderWhenActive(tab: string, content: unknown): unknown;
}

/**
 * A mixin that defers rendering each `<ak-tabs>` panel until it is first activated.
 *
 * `<ak-tabs>` keeps every panel in the light DOM, so without gating, every tab's
 * contents — and the API calls they trigger — would render up front. This holds
 * each panel back until its `@activate` event fires, then keeps it rendered.
 *
 * Usage:
 *
 * ```ts
 * export class MyTabs extends WithLazyTabs(AKElement) {
 *     // Pre-activate the default tab so it renders immediately.
 *     public override activatedTabs = new Set<string>(["page-a"]);
 *
 *     override render() {
 *         return html`<ak-tabs>
 *             <div slot="page-a" @activate=${() => this.activateTab("page-a")}>
 *                 ${this.renderWhenActive("page-a", html`<expensive-thing></expensive-thing>`)}
 *             </div>
 *         </ak-tabs>`;
 *     }
 * }
 * ```
 *
 * @category Mixin
 */
export const WithLazyTabs = createMixin<LazyTabsMixin>(({ SuperClass }) => {
    abstract class LazyTabsProvider extends SuperClass implements LazyTabsMixin {
        @state()
        public activatedTabs = new Set<string>();

        public activateTab(tab: string): void {
            if (this.activatedTabs.has(tab)) {
                return;
            }

            this.activatedTabs = new Set([...this.activatedTabs, tab]);
        }

        public renderWhenActive(tab: string, content: unknown): unknown {
            return this.activatedTabs.has(tab) ? content : null;
        }
    }

    return LazyTabsProvider;
});
