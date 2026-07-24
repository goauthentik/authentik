/**
 * @file A mixin that allows LitElements to monitor slots for content
 */

import { classList, ClassListDirective } from "#elements/directives/class-list";
import { createMixin } from "#elements/types";

import { css } from "lit";
import { DirectiveResult } from "lit-html/directive.js";

export interface SlottedContentCheckMixin {
    /**
     * The class name inserted into parent DOM objects whenever a contained slot changes and is
     * determined to be empty.
     */
    hideEmptySlotClassName: string;
    /**
     * A map of the token used to identify the *parent element* of a slot.
     */
    hasSlottedContent: Map<string, boolean>;
    /**
     * The function that updates `hasSlottedContent` whenever an evented slot changes.  To use,
     * set it on the slot: `<slot name="important" @slotchange=${this.checkForContent}></slot>`
     */
    checkForContent: (_event: Event) => void;
    /**
     * Helper function that returns a function that can be aliased to a short name and use in the
     * parent* DOM object to set/provide hide/show class when the child slot is empty.
     */
    provideContentHider: () => (_part: string) => DirectiveResult<typeof ClassListDirective>;
}

interface CheckForContentOptions {
    selector?: string;
    attribute?: string;
}

/**
 * The parent selector we look for, and the parent attribute we use to get a unique name for the
 *  slot's parent.  This allows us to target unnamed slots.
 */
const checkForContentOptionDefaults = {
    selector: "[part]",
    attribute: "part",
};

/**
 * This is the default behavior, and to get it this field must be included in a component's `styles`
 * field. `display: none` does not mean the slot isn't there; it is, and it will send out
 * `slotchange` events just fine.
 */
export const Zero = css`
    .hide-empty-slot-parent {
        display: none;
    }
`;

/**
 * A mixin that monitors slots for changes and, if the slot is empty, sets a class on the parent.
 * That class can be used to hide or modify the parent so that layout consequences of the empty slot
 * and its parent container can be mitigated. The default behavior sets a class which is associated
 * with the property `display: none`.
 *
 * By default, the selector `checkForContent` uses to identify the component affected by the slot
 * change is `.closest("[part]")`, and the attribute used to name the content is `part`.  A complete
 * use would look like:
 *
 * ```
 *  const hide = this.provideContentHider();
 *
 *     // ...
 *
 *     <div part="body" class=${hide("body")}>
 *         <slot name="body" @slotchange=${this.checkForContent}></slot>
 *     </div>
 * ```
 *
 * The class name, parent selector, and parent attribute are all configurable.  If you need multiple
 * dynamic classes in your parent selector, you may have to provide your own contentHider function.
 *
 */
export const WithSlottedContentCheck = createMixin<SlottedContentCheckMixin>(({ SuperClass }) => {
    abstract class SlottedContentCheckProvider
        extends SuperClass
        implements SlottedContentCheckMixin
    {
        public hideEmptySlotClassName = "hide-empty-slot-parent";

        public hasSlottedContent = new Map<string, boolean>();

        // Deliberately not named "onSlotChange"; this allows client code to get in front of this
        // event handler and do other things with the slot change event either before or after
        // including this handler in the event handler change.
        //
        public checkForContent = (event: Event, options?: CheckForContentOptions) => {
            const config: Required<CheckForContentOptions> = {
                ...checkForContentOptionDefaults,
                ...(options ? options : {}),
            };

            const target = event.target as HTMLSlotElement;
            const parent = target?.closest(config.selector);
            if (!parent) {
                console.warn(
                    `${this.tagName.toLowerCase()}: checkForContent: Could not find a named parent`,
                );
                return;
            }

            const identifier = parent.getAttribute(config.attribute);
            if (!identifier) {
                console.warn(
                    `${this.tagName.toLowerCase()}: checkForContent: Could not determine identifier for parent`,
                );
                return;
            }

            const nodes = target.assignedNodes({ flatten: true });
            const current = Boolean(this.hasSlottedContent.get(identifier));
            const has = nodes.some(
                (n) =>
                    n.nodeType === Node.ELEMENT_NODE ||
                    (n.nodeType === Node.TEXT_NODE && (n.textContent ?? "").trim().length > 0),
            );

            // It is important to change the visibility only when the value are discordant, otherwise
            // this could trigger an infinite loop of slot churn.
            if (has !== current) {
                this.hasSlottedContent.set(identifier, has);
                this.requestUpdate();
            }
        };

        public provideContentHider() {
            return (identifier: string) =>
                classList([!this.hasSlottedContent.get(identifier) && this.hideEmptySlotClassName]);
        }
    }

    return SlottedContentCheckProvider;
});
