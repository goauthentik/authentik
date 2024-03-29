import { EVENT_REFRESH } from "@goauthentik/authentik/common/constants";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { authentikConfigContext } from "@goauthentik/elements/AuthentikContexts";

import { ContextProvider } from "@lit/context";
import { ReactiveController, ReactiveControllerHost } from "lit";

import type { Config } from "@goauthentik/api";
import { RootApi } from "@goauthentik/api";

import type { AkInterface } from "./Interface";

type ReactiveElementHost = Partial<ReactiveControllerHost> & AkInterface;

export class ConfigContextController implements ReactiveController {
    host!: ReactiveElementHost;

    context!: ContextProvider<{ __context__: Config | undefined }>;

    constructor(host: ReactiveElementHost) {
        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: authentikConfigContext,
            initialValue: undefined,
        });
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
