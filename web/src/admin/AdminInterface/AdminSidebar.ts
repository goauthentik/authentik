import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_SIDEBAR_TOGGLE, VERSION } from "@goauthentik/common/constants";
import { me } from "@goauthentik/common/users";
import { AKElement } from "@goauthentik/elements/Base";
import {
    CapabilitiesEnum,
    WithCapabilitiesConfig,
} from "@goauthentik/elements/Interface/capabilitiesProvider";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "@goauthentik/elements/router/Route";
import { getRootStyle } from "@goauthentik/elements/utils/getRootStyle";
import { spread } from "@open-wc/lit-helpers";

import { msg, str } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import { AdminApi, CoreApi, UiThemeEnum, Version } from "@goauthentik/api";
import type { SessionUser, UserSelf } from "@goauthentik/api";

@customElement("ak-admin-sidebar")
export class AkAdminSidebar extends WithCapabilitiesConfig(AKElement) {
    @property({ type: Boolean, reflect: true })
    open = true;

    @state()
    version: Version["versionCurrent"] | null = null;

    @state()
    impersonation: UserSelf["username"] | null = null;

    constructor() {
        super();
        new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve().then((version) => {
            this.version = version.versionCurrent;
        });
        me().then((user: SessionUser) => {
            this.impersonation = user.original ? user.user.username : null;
        });
        this.toggleOpen = this.toggleOpen.bind(this);
        this.checkWidth = this.checkWidth.bind(this);
    }

    // This has to be a bound method so the event listener can be removed on disconnection as
    // needed.
    toggleOpen() {
        this.open = !this.open;
    }

    checkWidth() {
        // This works just fine, but it assumes that the `--ak-sidebar--minimum-auto-width` is in
        // REMs. If that changes, this code will have to be adjusted as well.
        const minWidth =
            parseFloat(getRootStyle("--ak-sidebar--minimum-auto-width")) *
            parseFloat(getRootStyle("font-size"));
        this.open = window.innerWidth >= minWidth;
    }

    connectedCallback() {
        super.connectedCallback();
        window.addEventListener(EVENT_SIDEBAR_TOGGLE, this.toggleOpen);
        window.addEventListener("resize", this.checkWidth);
        // After connecting to the DOM, we can now perform this check to see if the sidebar should
        // be open by default.
        this.checkWidth();
    }

    // The symmetry (☟, ☝) here is critical in that you want to start adding these handlers after
    // connection, and removing them before disconnection.

    disconnectedCallback() {
        window.removeEventListener(EVENT_SIDEBAR_TOGGLE, this.toggleOpen);
        window.removeEventListener("resize", this.checkWidth);
        super.disconnectedCallback();
    }

    render() {
        return html`
            <ak-sidebar
                class="pf-c-page__sidebar ${this.open ? "pf-m-expanded" : "pf-m-collapsed"} ${this
                    .activeTheme === UiThemeEnum.Light
                    ? "pf-m-light"
                    : ""}"
            >
                ${this.renderSidebarItems()}
            </ak-sidebar>
        `;
    }

    updated() {
        // This is permissible as`:host.classList` is not one of the properties Lit uses as a
        // scheduling trigger. This sort of shenanigans can trigger an loop, in that it will trigger
        // a browser reflow, which may trigger some other styling the application is monitoring,
        // triggering a re-render which triggers a browser reflow, ad infinitum. But we've been
        // living with that since jQuery, and it's both well-known and fortunately rare.
        this.classList.remove("pf-m-expanded", "pf-m-collapsed");
        this.classList.add(this.open ? "pf-m-expanded" : "pf-m-collapsed");
    }

    renderSidebarItems(): TemplateResult {
        // The second attribute type is of string[] to help with the 'activeWhen' control, which was
        // commonplace and singular enough to merit its own handler.
        type SidebarEntry = [
            path: string | null,
            label: string,
            attributes?: Record<string, any> | string[] | null, // eslint-disable-line
            children?: SidebarEntry[],
        ];

        // prettier-ignore
        const sidebarContent: SidebarEntry[] = [
            ["/if/user/", msg("User interface"), { "?isAbsoluteLink": true, "?highlight": true }],
            [null, msg("Dashboards"), { "?expanded": true }, [
                ["/administration/overview", msg("Overview")],
                ["/administration/dashboard/users", msg("User Statistics")],
                ["/administration/system-tasks", msg("System Tasks")]]],
            [null, msg("Applications"), null, [
                ["/core/applications", msg("Applications"), [`^/core/applications/(?<slug>${SLUG_REGEX})$`]],
                ["/core/providers", msg("Providers"), [`^/core/providers/(?<id>${ID_REGEX})$`]],
                ["/outpost/outposts", msg("Outposts")]]],
            [null, msg("Events"), null, [
                ["/events/log", msg("Logs"), [`^/events/log/(?<id>${UUID_REGEX})$`]],
                ["/events/rules", msg("Notification Rules")],
                ["/events/transports", msg("Notification Transports")]]],
            [null, msg("Customisation"), null, [
                ["/policy/policies", msg("Policies")],
                ["/core/property-mappings", msg("Property Mappings")],
                ["/blueprints/instances", msg("Blueprints")],
                ["/policy/reputation", msg("Reputation scores")]]],
            [null, msg("Flows and Stages"), null, [
                ["/flow/flows", msg("Flows"), [`^/flow/flows/(?<slug>${SLUG_REGEX})$`]],
                ["/flow/stages", msg("Stages")],
                ["/flow/stages/prompts", msg("Prompts")]]],
            [null, msg("Directory"), null, [
                ["/identity/users", msg("Users"), [`^/identity/users/(?<id>${ID_REGEX})$`]],
                ["/identity/groups", msg("Groups"), [`^/identity/groups/(?<id>${UUID_REGEX})$`]],
                ["/identity/roles", msg("Roles"), [`^/identity/roles/(?<id>${UUID_REGEX})$`]],
                ["/core/sources", msg("Federation and Social login"), [`^/core/sources/(?<slug>${SLUG_REGEX})$`]],
                ["/core/tokens", msg("Tokens and App passwords")],
                ["/flow/stages/invitations", msg("Invitations")]]],
            [null, msg("System"), null, [
                ["/core/brands", msg("Brands")],
                ["/crypto/certificates", msg("Certificates")],
                ["/outpost/integrations", msg("Outpost Integrations")],
                ["/admin/settings", msg("Settings")]]],
        ];

        // Typescript requires the type here to correctly type the recursive path
        type SidebarRenderer = (_: SidebarEntry) => TemplateResult;

        const renderOneSidebarItem: SidebarRenderer = ([path, label, attributes, children]) => {
            const properties = Array.isArray(attributes)
                ? { ".activeWhen": attributes }
                : attributes ?? {};
            if (path) {
                properties["path"] = path;
            }
            return html`<ak-sidebar-item ${spread(properties)}>
                ${label ? html`<span slot="label">${label}</span>` : nothing}
                ${map(children, renderOneSidebarItem)}
            </ak-sidebar-item>`;
        };

        // prettier-ignore
        return html`
            ${this.renderNewVersionMessage()}
            ${this.renderImpersonationMessage()}
            ${map(sidebarContent, renderOneSidebarItem)}
            ${this.renderEnterpriseMessage()}
        `;
    }

    renderNewVersionMessage() {
        return this.version && this.version !== VERSION
            ? html`
                  <ak-sidebar-item ?highlight=${true}>
                      <span slot="label"
                          >${msg("A newer version of the frontend is available.")}</span
                      >
                  </ak-sidebar-item>
              `
            : nothing;
    }

    renderImpersonationMessage() {
        const reload = () =>
            new CoreApi(DEFAULT_CONFIG).coreUsersImpersonateEndRetrieve().then(() => {
                window.location.reload();
            });

        return this.impersonation
            ? html`<ak-sidebar-item ?highlight=${true} @click=${reload}>
                  <span slot="label"
                      >${msg(
                          str`You're currently impersonating ${this.impersonation}. Click to stop.`,
                      )}</span
                  >
              </ak-sidebar-item>`
            : nothing;
    }

    renderEnterpriseMessage() {
        return this.can(CapabilitiesEnum.IsEnterprise)
            ? html`
                  <ak-sidebar-item>
                      <span slot="label">${msg("Enterprise")}</span>
                      <ak-sidebar-item path="/enterprise/licenses">
                          <span slot="label">${msg("Licenses")}</span>
                      </ak-sidebar-item>
                  </ak-sidebar-item>
              `
            : nothing;
    }
}
