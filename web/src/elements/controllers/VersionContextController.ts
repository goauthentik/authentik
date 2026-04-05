import { DEFAULT_CONFIG } from "#common/api/config";
import { isGuest } from "#common/users";

import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { SessionMixin } from "#elements/mixins/session";
import { VersionContext, VersionMixin } from "#elements/mixins/version";
import type { ReactiveElementHost } from "#elements/types";

import { AdminApi, Version } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";

export class VersionContextController extends ReactiveContextController<Version> {
    protected static override logPrefix = "version";

    public host: ReactiveElementHost<SessionMixin & VersionMixin>;
    public context: ContextProvider<VersionContext>;

    constructor(host: ReactiveElementHost<SessionMixin & VersionMixin>, initialValue?: Version) {
        super();

        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: VersionContext,
            initialValue,
        });
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        return new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve(requestInit);
    }

    protected doRefresh(version: Version) {
        this.context.setValue(version);
        this.host.version = version;
    }

    public hostUpdate() {
        const { currentUser } = this.host;

        if (currentUser && !isGuest(currentUser) && !this.host.version && !this.abortController) {
            this.refresh();

            return;
        }

        if (!currentUser) {
            this.abort("Session Invalidated");
        }
    }
}
