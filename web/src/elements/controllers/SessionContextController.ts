import { DEFAULT_CONFIG } from "#common/api/config";
import { type APIResult, isAPIResultReady } from "#common/api/responses";
import { globalAK } from "#common/global";
import { applyThemeChoice, formatColorScheme } from "#common/theme";
import { createUIConfig, DefaultUIConfig } from "#common/ui/config";
import { autoDetectLanguage } from "#common/ui/locale/utils";
import { me } from "#common/users";

import { CommandPaletteState, PaletteCommandDefinition } from "#elements/commands/shared";
import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { AKConfigMixin, kAKConfig } from "#elements/mixins/config";
import { kAKLocale, type LocaleMixin } from "#elements/mixins/locale";
import {
    canAccessAdmin,
    SessionContext,
    SessionMixin,
    UIConfigContext,
} from "#elements/mixins/session";
import { AKDrawerChangeEvent } from "#elements/notifications/events";
import type { ReactiveElementHost } from "#elements/types";

import { CoreApi, SessionUser } from "@goauthentik/api";

import { setUser } from "@sentry/browser";

import { ContextProvider } from "@lit/context";
import { msg } from "@lit/localize";

/**
 * A controller that provides the session information to the element.
 *
 * @see {@linkcode SessionMixin}
 */
export class SessionContextController extends ReactiveContextController<APIResult<SessionUser>> {
    protected static override logPrefix = "session";

    public host: ReactiveElementHost<LocaleMixin & SessionMixin & AKConfigMixin>;
    public context: ContextProvider<SessionContext>;

    protected uiConfigContext: ContextProvider<UIConfigContext>;

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

        this.uiConfigContext = new ContextProvider(this.host, {
            context: UIConfigContext,
            initialValue: DefaultUIConfig,
        });
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        return me(requestInit);
    }

    #refreshCommandsFrameID = -1;

    #commands = new CommandPaletteState({
        target: this.host,
    });

    protected doRefresh(session: APIResult<SessionUser>): void {
        this.context.setValue(session);
        this.host.session = session;

        if (!isAPIResultReady(session)) return;

        const localeHint: string | undefined = session.user.settings.locale;

        if (localeHint) {
            const locale = autoDetectLanguage(localeHint);
            this.logger.info(`Activating user's configured locale '${locale}'`);
            this.host[kAKLocale]?.setLocale(locale);
        }

        const { settings = {} } = session.user || {};

        const nextUIConfig = createUIConfig(settings);
        this.uiConfigContext.setValue(nextUIConfig);
        this.host.uiConfig = nextUIConfig;
        const colorScheme = formatColorScheme(nextUIConfig.theme.base);

        applyThemeChoice(colorScheme, this.host.ownerDocument);

        const config = this.host[kAKConfig];

        if (config?.errorReporting.sendPii) {
            this.logger.info("Sentry with PII enabled.");

            setUser({ email: session.user.email });
        }

        this.#refreshCommandsFrameID = requestAnimationFrame(this.#refreshCommands);
    }

    #refreshCommands = (): void => {
        const session = this.context.value;

        if (!isAPIResultReady(session)) {
            this.#commands.clear();
            return;
        }

        const base = globalAK().api.base;
        const group = msg("Session");

        const commands: PaletteCommandDefinition[] = [
            {
                label: msg("Sign out"),
                suffix: msg("Reloads page", { id: "command-palette.prefix.reloads-page" }),
                keywords: [msg("Logout"), msg("Log off"), msg("Sign off")],
                group,
                action: () => {
                    window.location.assign(`${base}flows/-/default/invalidation/`);
                },
            },
            {
                label: msg("User settings"),
                prefix: msg("Navigate to", { id: "command-palette.prefix.navigate" }),
                group,
                action: () => {
                    window.location.assign(`${base}if/user/#/settings`);
                },
            },
        ];

        const { notificationDrawer, apiDrawer } = this.host.uiConfig?.enabledFeatures ?? {};
        const drawerGroup = msg("Interface");

        if (apiDrawer) {
            commands.push({
                label: msg("API requests drawer", {
                    id: "command-palette.label.api-requests-drawer",
                }),
                prefix: msg("Toggle", { id: "command-palette.prefix.toggle" }),
                group: drawerGroup,
                action: AKDrawerChangeEvent.dispatchAPIToggle,
            });
        }

        if (notificationDrawer) {
            commands.push({
                label: msg("Notifications drawer", {
                    id: "command-palette.label.notifications-drawer",
                }),
                prefix: msg("Toggle", { id: "command-palette.prefix.toggle" }),
                group: drawerGroup,
                action: AKDrawerChangeEvent.dispatchNotificationsToggle,
            });
        }

        if (canAccessAdmin(session.user)) {
            commands.push({
                label: msg("Admin interface"),
                prefix: msg("Navigate to", { id: "command-palette.prefix.navigate" }),
                group,
                action: () => {
                    window.location.assign(`${base}if/admin/`);
                },
            });
        }

        if (session.original) {
            commands.push({
                label: msg("Stop impersonation"),
                suffix: msg("Reloads page", { id: "command-palette.prefix.reloads-page" }),
                group,
                action: async () => {
                    await new CoreApi(DEFAULT_CONFIG).coreUsersImpersonateEndRetrieve();
                    window.location.reload();
                },
            });
        }

        this.#commands.set(commands);
    };

    public override hostConnected() {
        this.logger.debug("Host connected, refreshing session");
        this.refresh();
    }

    public override hostDisconnected() {
        this.context.clearCallbacks();
        cancelAnimationFrame(this.#refreshCommandsFrameID);

        super.hostDisconnected();
    }
}
