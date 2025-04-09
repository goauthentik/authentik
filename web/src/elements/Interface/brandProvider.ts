import { authentikBrandContext } from "@goauthentik/elements/AuthentikContexts";
import { createMixin } from "@goauthentik/elements/types";

import { consume } from "@lit/context";
import { state } from "lit/decorators.js";

import type { CurrentBrand } from "@goauthentik/api";

/**
 * A mixin that provides the current brand to the element.
 */
export interface StyleBrandMixin {
    /**
     * The current style branding configuration.
     */
    brand: CurrentBrand;
}

/**
 * A mixin that provides the current brand to the element.
 *
 * @category Mixin
 *
 * @see {@link https://lit.dev/docs/composition/mixins/#mixins-in-typescript | Lit Mixins}
 */
export const WithBrandConfig = createMixin<StyleBrandMixin>(
    ({
        /**
         * The superclass constructor to extend.
         */
        SuperClass,
        /**
         * Whether or not to subscribe to the context.
         */
        subscribe = true,
    }) => {
        abstract class StyleBrandProvider extends SuperClass implements StyleBrandMixin {
            @consume({
                context: authentikBrandContext,
                subscribe,
            })
            @state()
            public brand!: CurrentBrand;
        }

        return StyleBrandProvider;
    },
);
