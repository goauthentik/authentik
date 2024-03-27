import { EVENT_REFRESH } from "@goauthentik/authentik/common/constants";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { authentikBrandContext } from "@goauthentik/elements/AuthentikContexts";

import { ContextProvider } from "@lit/context";
import { ReactiveController, ReactiveControllerHost } from "lit";

import type { CurrentBrand } from "@goauthentik/api";
import { CoreApi } from "@goauthentik/api";

import type { AkInterface } from "./Interface";

type ReactiveElementHost = Partial<ReactiveControllerHost> & AkInterface;

export class BrandContextController implements ReactiveController {
    host!: ReactiveElementHost;

    context!: ContextProvider<{ __context__: CurrentBrand | undefined }>;

    constructor(host: ReactiveElementHost) {
        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: authentikBrandContext,
            initialValue: undefined,
        });
        this.fetch = this.fetch.bind(this);
        this.fetch();
    }

    fetch() {
        new CoreApi(DEFAULT_CONFIG).coreBrandsCurrentRetrieve().then((brand) => {
            this.context.setValue(brand);
            this.host.brand = brand;
        });
    }

    hostConnected() {
        window.addEventListener(EVENT_REFRESH, this.fetch);
    }

    hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.fetch);
    }

    hostUpdate() {
        // If the Interface changes its brand information for some reason,
        // we should notify all users of the context of that change. doesn't
        if (this.host.brand !== this.context.value) {
            this.context.setValue(this.host.brand);
        }
    }
}
