import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import { ThemedElement } from "@goauthentik/common/theme";
import { authentikConfigContext } from "@goauthentik/elements/AuthentikContexts";
import type { ReactiveElementHost } from "@goauthentik/elements/types.js";

import { ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

import type { Config } from "@goauthentik/api";
import { RootApi } from "@goauthentik/api";

export class ConfigContextController implements ReactiveController {
    host!: ReactiveElementHost<ThemedElement>;

    context!: ContextProvider<{ __context__: Config | undefined }>;

    constructor(host: ReactiveElementHost<ThemedElement>) {
        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: authentikConfigContext,
            initialValue: undefined,
        });
        // Pre-hydrate from template-embedded config
        this.context.setValue(globalAK().config);
        this.host.config = globalAK().config;
        this.fetch = this.fetch.bind(this);
        this.fetch();
    }

    fetch() {
        new RootApi(DEFAULT_CONFIG).rootConfigRetrieve().then((config) => {
            this.context.setValue(config);
            this.host.config = config;
        });
    }

    hostConnected() {
        window.addEventListener(EVENT_REFRESH, this.fetch);
    }

    hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.fetch);
    }

    hostUpdate() {
        // If the Interface changes its config information, we should notify all
        // users of the context of that change, without creating an infinite
        // loop of resets.
        if (this.host.config !== this.context.value) {
            this.context.setValue(this.host.config);
        }
    }
}
