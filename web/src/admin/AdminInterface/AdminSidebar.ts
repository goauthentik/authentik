import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_SIDEBAR_TOGGLE, VERSION } from "@goauthentik/common/constants";
import { eventActionLabels } from "@goauthentik/common/labels";
import { me } from "@goauthentik/common/users";
import { AKElement } from "@goauthentik/elements/Base";
import {
    CapabilitiesEnum,
    WithCapabilitiesConfig,
} from "@goauthentik/elements/Interface/capabilitiesProvider";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "@goauthentik/elements/router/Route";
import "@goauthentik/elements/sidebar/Sidebar";
import {
    SidebarAttributes,
    SidebarEntry,
    SidebarEventHandler,
} from "@goauthentik/elements/sidebar/types";
import { getRootStyle } from "@goauthentik/elements/utils/getRootStyle";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { AdminApi } from "@goauthentik/api";
import { CoreApi, Version } from "@goauthentik/api";
import type { SessionUser, UserSelf } from "@goauthentik/api";

import { flowDesignationTable } from "../flows/utils";
import ConnectionTypesController from "./SidebarEntries/ConnectionTypesController";
import PolicyTypesController from "./SidebarEntries/PolicyTypesController";
import PropertyMappingsController from "./SidebarEntries/PropertyMappingsController";
import ProviderTypesController from "./SidebarEntries/ProviderTypesController";
import SourceTypesController from "./SidebarEntries/SourceTypesController";
import StageTypesController from "./SidebarEntries/StageTypesController";

/**
 * AdminSidebar
 *
 * The AdminSidebar has two responsibilities:
 *
 * 1. Control the styling of the sidebar host, specifically when to show it and whether to show
 *    it as an overlay or as a push.
 * 2. Control what content the sidebar will receive.  The sidebar takes a tree, maximally three deep,
 *    of type SidebarEventHandler.
 */

type SidebarUrl = string;

export type LocalSidebarEntry = [
    // - null: This entry is not a link.
    // - string: the url for the entry
    // - SidebarEventHandler: a function to run if the entry is clicked.
    SidebarUrl | SidebarEventHandler | null,
    // The visible text of the entry.
    string,
    // Attributes to which the sidebar responds. See the sidebar for details.
    (SidebarAttributes | string[] | null)?, // eslint-disable-line
    // Children of the entry
    LocalSidebarEntry[]?,
];

const localToSidebarEntry = (l: LocalSidebarEntry): SidebarEntry => ({
    path: l[0],
    label: l[1],
    ...(l[2] ? { attributes: Array.isArray(l[2]) ? { activeWhen: l[2] } : l[2] } : {}),
    ...(l[3] ? { children: l[3].map(localToSidebarEntry) } : {}),
});

@customElement("ak-admin-sidebar")
export class AkAdminSidebar extends WithCapabilitiesConfig(AKElement) {
    @property({ type: Boolean, reflect: true })
    open = true;

    @state()
    version: Version["versionCurrent"] | null = null;

    @state()
    impersonation: UserSelf["username"] | null = null;

    private connectionTypes = new ConnectionTypesController(this);
    private policyTypes = new PolicyTypesController(this);
    private propertyMapper = new PropertyMappingsController(this);
    private providerTypes = new ProviderTypesController(this);
    private sourceTypes = new SourceTypesController(this);
    private stageTypes = new StageTypesController(this);

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

    updated() {
        // This is permissible as`:host.classList` is not one of the properties Lit uses as a
        // scheduling trigger. This sort of shenanigans can trigger an loop, in that it will trigger
        // a browser reflow, which may trigger some other styling the application is monitoring,
        // triggering a re-render which triggers a browser reflow, ad infinitum. But we've been
        // living with that since jQuery, and it's both well-known and fortunately rare.
        this.classList.remove("pf-m-expanded", "pf-m-collapsed");
        this.classList.add(this.open ? "pf-m-expanded" : "pf-m-collapsed");
    }

    get sidebarItems(): SidebarEntry[] {
        const reload = () =>
            new CoreApi(DEFAULT_CONFIG).coreUsersImpersonateEndRetrieve().then(() => {
                window.location.reload();
            });

        // prettier-ignore
        const newVersionMessage: LocalSidebarEntry[] =
            this.version && this.version !== VERSION
                ? [[ "https://goauthentik.io", msg("A newer version of the frontend is available."),
                     { highlight: true }]]
                : [];

        // prettier-ignore
        const impersonationMessage: LocalSidebarEntry[] = this.impersonation
            ? [[reload, msg(str`You're currently impersonating ${this.impersonation}. Click to stop.`)]]
            : [];

        // prettier-ignore
        const enterpriseMenu: LocalSidebarEntry[] = this.can(CapabilitiesEnum.IsEnterprise)
            ? [[null, msg("Enterprise"), null, [["/enterprise/licenses", msg("Licenses")]]]]
            : [];

        const flowTypes: LocalSidebarEntry[] = flowDesignationTable.map(([_designation, label]) => [
            `/flow/flows;${encodeURIComponent(JSON.stringify({ search: label }))}`,
            label,
        ]);

        const eventTypes: LocalSidebarEntry[] = eventActionLabels.map(([_action, label]) => [
            `/events/log;${encodeURIComponent(JSON.stringify({ search: label }))}`,
            label,
        ]);

        // prettier-ignore
        const localSidebar: LocalSidebarEntry[] = [
            ...(newVersionMessage),
            ...(impersonationMessage),
            ["/if/user/", msg("User interface"), { isAbsoluteLink: true, highlight: true }],
            [null, msg("Dashboards"), { expanded: true }, [
                ["/administration/overview", msg("Overview")],
                ["/administration/dashboard/users", msg("User Statistics")],
                ["/administration/system-tasks", msg("System Tasks")]]],
            [null, msg("Applications"), null, [
                ["/core/applications", msg("Applications"), [`^/core/applications(/(?<slug>${SLUG_REGEX}))?$`]],
                ["/core/providers", msg("Providers"), [`^/core/providers(/(?<id>${ID_REGEX}))?$`], this.providerTypes.entries()],
                ["/outpost/outposts", msg("Outposts")]]],
            [null, msg("Events"), null, [
                ["/events/log", msg("Logs"), [`^/events/log(/(?<id>${UUID_REGEX}))?$`], eventTypes],
                ["/events/rules", msg("Notification Rules")],
                ["/events/transports", msg("Notification Transports")]]],
            [null, msg("Customisation"), null, [
                ["/policy/policies", msg("Policies"), null, this.policyTypes.entries()],
                ["/core/property-mappings", msg("Property Mappings"), null, this.propertyMapper.entries()],
                ["/blueprints/instances", msg("Blueprints")],
                ["/policy/reputation", msg("Reputation scores")]]],
            [null, msg("Flows and Stages"), null, [
                ["/flow/flows", msg("Flows"), [`^/flow/flows(/(?<slug>${SLUG_REGEX}))?$`], flowTypes],
                ["/flow/stages", msg("Stages"), null, this.stageTypes.entries()],
                ["/flow/stages/prompts", msg("Prompts")]]],
            [null, msg("Directory"), null, [
                ["/identity/users", msg("Users"), [`^/identity/users(/(?<id>${ID_REGEX}))?$`]],
                ["/identity/groups", msg("Groups"), [`^/identity/groups(/(?<id>${UUID_REGEX}))?$`]],
                ["/identity/roles", msg("Roles"), [`^/identity/roles/(?<id>${UUID_REGEX})$`]],
                ["/core/sources", msg("Federation and Social login"), [`^/core/sources(/(?<slug>${SLUG_REGEX}))?$`], this.sourceTypes.entries()],
                ["/core/tokens", msg("Tokens and App passwords")],
                ["/flow/stages/invitations", msg("Invitations")]]],
             [null, msg("System"), null, [
                 ["/core/brands", msg("Brands")],
                 ["/crypto/certificates", msg("Certificates")],
                 ["/outpost/integrations", msg("Outpost Integrations"), null, this.connectionTypes.entries()],
                 ["/admin/settings", msg("Settings")]]],
            ...(enterpriseMenu)
        ];

        return localSidebar.map(localToSidebarEntry);
    }

    render() {
        return html`
            <ak-sidebar class="pf-c-page__sidebar" .entries=${this.sidebarItems}></ak-sidebar>
        `;
    }
}
