import { DEFAULT_CONFIG } from "#common/api/config";

import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { BrandingContext, BrandingMixin } from "#elements/mixins/branding";
import type { ReactiveElementHost } from "#elements/types";

import { CoreApi, CurrentBrand } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";

export class BrandingContextController extends ReactiveContextController<CurrentBrand> {
    protected static override logPrefix = "branding";

    public host: ReactiveElementHost<BrandingMixin>;
    public context: ContextProvider<BrandingContext>;

    constructor(host: ReactiveElementHost<BrandingMixin>, initialValue: CurrentBrand) {
        super();

        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: BrandingContext,
            initialValue,
        });
        this.host.brand = initialValue;
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        return new CoreApi(DEFAULT_CONFIG).coreBrandsCurrentRetrieve(requestInit);
    }

    protected doRefresh(brand: CurrentBrand) {
        this.context.setValue(brand);
        this.host.brand = brand;
    }

    public hostUpdate() {
        // If the Interface changes its brand information for some reason,
        // we should notify all users of the context of that change. doesn't
        if (this.host.brand && this.host.brand !== this.context.value) {
            this.context.setValue(this.host.brand);
        }
    }
}
