import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { authentikVersionContext } from "@goauthentik/elements/AuthentikContexts";
import type { ReactiveElementHost } from "@goauthentik/elements/types.js";

import { ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

import type { Version } from "@goauthentik/api";
import { AdminApi } from "@goauthentik/api";

import type { AkAuthenticatedInterface } from "./Interface";

export class VersionContextController implements ReactiveController {
    host!: ReactiveElementHost<AkAuthenticatedInterface>;

    context!: ContextProvider<{ __context__: Version | undefined }>;

    constructor(host: ReactiveElementHost<AkAuthenticatedInterface>) {
        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: authentikVersionContext,
            initialValue: undefined,
        });
        this.fetch = this.fetch.bind(this);
        this.fetch();
    }

    fetch() {
        new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve().then((version) => {
            this.context.setValue(version);
            this.host.version = version;
        });
    }

    hostConnected() {
        window.addEventListener(EVENT_REFRESH, this.fetch);
    }

    hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.fetch);
    }

    hostUpdate() {
        // If the Interface changes its version information for some reason,
        // we should notify all users of the context of that change. doesn't
        if (this.host.version !== this.context.value) {
            this.context.setValue(this.host.version);
        }
    }
}
