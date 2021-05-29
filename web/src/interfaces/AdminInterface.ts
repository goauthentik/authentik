import "../elements/messages/MessageContainer";
import { customElement, html, TemplateResult } from "lit-element";
import { me } from "../api/Users";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "../elements/router/Route";
import { Interface } from "./Interface";
import "./locale";
import "../elements/sidebar/SidebarItem";
import { t } from "@lingui/macro";

@customElement("ak-interface-admin")
export class AdminInterface extends Interface {

    renderSidebarItems(): TemplateResult {
        const superUserCondition = () => {
            return me().then(u => u.user.isSuperuser || false);
        };
        return html`
            <ak-sidebar-item path="/library">
                <span slot="label">${t`Library`}</span>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Monitor`}</span>
                <ak-sidebar-item path="/administration/overview">
                    <span slot="label">${t`Overview`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/administration/system-tasks">
                    <span slot="label">${t`System Tasks`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Resources`}</span>
                <ak-sidebar-item path="/core/applications" .activeWhen=${[`^/core/applications/(?<slug>${SLUG_REGEX})$`]}>
                    <span slot="label">${t`Applications`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/sources" .activeWhen=${[`^/core/sources/(?<slug>${SLUG_REGEX})$`]}>
                    <span slot="label">${t`Sources`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/providers" .activeWhen=${[`^/core/providers/(?<id>${ID_REGEX})$`]}>
                    <span slot="label">${t`Providers`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/tenants">
                    <span slot="label">${t`Tenants`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Outposts`}</span>
                <ak-sidebar-item path="/outpost/outposts">
                    <span slot="label">${t`Outposts`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/outpost/service-connections">
                    <span slot="label">${t`Service Connections`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Events`}</span>
                <ak-sidebar-item path="/events/log" .activeWhen=${[`^/events/log/(?<id>${UUID_REGEX})$`]}>
                    <span slot="label">${t`Logs`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/events/rules">
                    <span slot="label">${t`Notification Rules`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/events/transports">
                    <span slot="label">${t`Notification Transports`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Customisation`}</span>
                <ak-sidebar-item path="/policy/policies">
                    <span slot="label">${t`Policies`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/property-mappings">
                    <span slot="label">${t`Property Mappings`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Flows`}</span>
                <ak-sidebar-item path="/flow/flows" .activeWhen=${[`^/flow/flows/(?<slug>${SLUG_REGEX})$`]}>
                    <span slot="label">${t`Flows`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages">
                    <span slot="label">${t`Stages`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages/prompts">
                    <span slot="label">${t`Prompts`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages/invitations">
                    <span slot="label">${t`Invitations`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item
                .condition=${superUserCondition}>
                <span slot="label">${t`Identity & Cryptography`}</span>
                <ak-sidebar-item path="/identity/users" .activeWhen=${[`^/identity/users/(?<id>${ID_REGEX})$`]}>
                    <span slot="label">${t`Users`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/identity/groups">
                    <span slot="label">${t`Groups`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/crypto/certificates">
                    <span slot="label">${t`Certificates`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/tokens">
                    <span slot="label">${t`Tokens`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
        `;
    }

}
