import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import type { ReactiveElementHost } from "@goauthentik/elements/types.js";
import { createMixin } from "@goauthentik/elements/utils/mixins";
import { ThemedElement } from "@goauthentik/elements/utils/theme";

import { consume, createContext } from "@lit/context";
import { Context, ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";
import { state } from "lit/decorators.js";

import type { CurrentBrand } from "@goauthentik/api";
import { CoreApi } from "@goauthentik/api";

export const authentikBrandContext = createContext<CurrentBrand>(Symbol("authentik-brand-context"));

export class BrandController implements ReactiveController {
    readonly #host: ReactiveElementHost<ThemedElement>;
    readonly #context: ContextProvider<Context<unknown, CurrentBrand | undefined>>;

    constructor(host: ReactiveElementHost<ThemedElement>) {
        this.#host = host;

        const { brand } = globalAK();

        this.#context = new ContextProvider(this.#host, {
            context: authentikBrandContext,
            initialValue: brand,
        });

        this.refresh();
    }

    public refresh = () => {
        return new CoreApi(DEFAULT_CONFIG).coreBrandsCurrentRetrieve().then((brand) => {
            this.#context.setValue(brand);
            this.#host.brand = brand;
        });
    };

    public hostConnected() {
        window.addEventListener(EVENT_REFRESH, this.refresh);
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.refresh);
    }

    public hostUpdate() {
        // If the Interface changes its brand information for some reason,
        // we should notify all users of the context of that change. doesn't
        if (this.#host.brand !== this.#context.value) {
            this.#context.setValue(this.#host.brand);
        }
    }
}

/**
 * A mixin that provides the current brand to the element.
 */
export interface BrandConsumer {
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
export const WithBrandConfig = createMixin<BrandConsumer>(
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
        abstract class StyleBrandProvider extends SuperClass implements BrandConsumer {
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
