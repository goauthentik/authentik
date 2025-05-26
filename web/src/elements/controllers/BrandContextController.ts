import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { isAbortError } from "#common/errors/network";
import { BrandingContext, BrandingMixin } from "#elements/mixins/branding";
import type { ReactiveElementHost } from "#elements/types";

import { Context, ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

import { CoreApi, CurrentBrand } from "@goauthentik/api";

export class BrandingContextController implements ReactiveController {
    #log = console.debug.bind(console, `authentik/controller/branding`);
    #abortController: null | AbortController = null;

    #host: ReactiveElementHost<BrandingMixin>;
    #context: ContextProvider<Context<unknown, CurrentBrand>>;

    constructor(host: ReactiveElementHost<BrandingMixin>, initialValue: CurrentBrand) {
        this.#host = host;
        this.#context = new ContextProvider(this.#host, {
            context: BrandingContext,
            initialValue,
        });
        this.#host.brand = initialValue;
    }

    #fetch = () => {
        this.#log("Fetching configuration...");

        this.#abortController?.abort();

        this.#abortController = new AbortController();

        return new CoreApi(DEFAULT_CONFIG)
            .coreBrandsCurrentRetrieve({
                signal: this.#abortController.signal,
            })
            .then((brand) => {
                this.#context.setValue(brand);
                this.#host.brand = brand;
            })

            .catch((error: unknown) => {
                if (isAbortError(error)) {
                    this.#log("Aborted fetching brand");
                    return;
                }

                throw error;
            })
            .finally(() => {
                this.#abortController = null;
            });
    };

    public hostConnected() {
        window.addEventListener(EVENT_REFRESH, this.#fetch);
        this.#fetch();
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.#fetch);
        this.#abortController?.abort();
    }

    public hostUpdate() {
        // If the Interface changes its brand information for some reason,
        // we should notify all users of the context of that change. doesn't
        if (this.#host.brand && this.#host.brand !== this.#context.value) {
            this.#context.setValue(this.#host.brand);
        }
    }
}
