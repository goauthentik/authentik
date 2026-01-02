import { type APIResult, isAPIResultReady } from "#common/api/responses";
import { autoDetectLanguage } from "#common/ui/locale/utils";
import { me } from "#common/users";

import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { AKConfigMixin, kAKConfig } from "#elements/mixins/config";
import { kAKLocale, type LocaleMixin } from "#elements/mixins/locale";
import { SessionContext, SessionMixin } from "#elements/mixins/session";
import type { ReactiveElementHost } from "#elements/types";

import { SessionUser } from "@goauthentik/api";

import { setUser } from "@sentry/browser";

import { ContextProvider } from "@lit/context";

/**
 * A controller that provides the session information to the element.
 *
 * @see {@linkcode SessionMixin}
 */
export class SessionContextController extends ReactiveContextController<APIResult<SessionUser>> {
    protected static override logPrefix = "session";

    public host: ReactiveElementHost<LocaleMixin & SessionMixin & AKConfigMixin>;
    public context: ContextProvider<SessionContext>;

    constructor(
        host: ReactiveElementHost<SessionMixin & AKConfigMixin>,
        initialValue?: APIResult<SessionUser>,
    ) {
        super();

        this.host = host;

        this.context = new ContextProvider(this.host, {
            context: SessionContext,
            initialValue: initialValue ?? { loading: true, error: null },
        });
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        return me(requestInit);
    }

    protected doRefresh(session: APIResult<SessionUser>) {
        this.context.setValue(session);
        this.host.session = session;

        if (isAPIResultReady(session)) {
            const localeHint: string | undefined = session.user.settings.locale;

            if (localeHint) {
                const locale = autoDetectLanguage(localeHint);
                this.debug(`Activating user's configured locale '${locale}'`);
                this.host[kAKLocale]?.setLocale(locale);
            }

            const config = this.host[kAKConfig];

            if (config?.errorReporting.sendPii) {
                this.debug("Sentry with PII enabled.");

                setUser({ email: session.user.email });
            }
        }
    }

    public override hostConnected() {
        this.debug("Host connected, refreshing session");
        this.refresh();
    }

    public override hostDisconnected() {
        this.context.clearCallbacks();

        super.hostDisconnected();
    }
}
