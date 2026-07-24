/**
 * @file A mixin that allows LitElements to monitor slots for content
 */

import { classList, ClassListDirective } from "#elements/directives/class-list";
import { createMixin } from "#elements/types";

import { css } from "lit";
import { DirectiveResult } from "lit-html/directive.js";

export interface SlottedContentCheckMixin {
    hasSlottedContent: Map<string, boolean>;
    checkForContent: (_event: Event) => void;
    provideContentHider: () => (_part: string) => DirectiveResult<typeof ClassListDirective>;
}

interface CheckForContentOptions {
    selector?: string;
    attribute?: string;
}

const checkForContentOptionDefaults = {
    selector: "[part]",
    attribute: "part",
};

// `display: none` does not mean the slot isn't there.
export const Zero = css`
    .hide-empty-slot-parent {
        display: none;
    }
`;

export const WithSlottedContentCheck = createMixin<SlottedContentCheckMixin>(({ SuperClass }) => {
    abstract class SlottedContentCheckProvider
        extends SuperClass
        implements SlottedContentCheckMixin
    {
        public hasSlottedContent = new Map<string, boolean>();

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
            if (has !== current) {
                this.hasSlottedContent.set(identifier, has);
                this.requestUpdate();
            }
        };

        public provideContentHider() {
            return (identifier: string) =>
                classList([!this.hasSlottedContent.get(identifier) && "hide-empty-slot-parent"]);
        }
    }

    return SlottedContentCheckProvider;
});
