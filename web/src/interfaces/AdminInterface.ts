import "../elements/messages/MessageContainer";
import { customElement } from "lit-element";
import { me } from "../api/Users";
import { SidebarItem } from "../elements/sidebar/Sidebar";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "../elements/router/Route";
import { Interface } from "./Interface";
import "./locale";
import { t } from "@lingui/macro";

export const SIDEBAR_ITEMS: SidebarItem[] = [
    new SidebarItem(t`Library`, "/library"),
    new SidebarItem(t`Monitor`).children(
        new SidebarItem(t`Overview`, "/administration/overview"),
        new SidebarItem(t`System Tasks`, "/administration/system-tasks"),
    ).when((): Promise<boolean> => {
        return me().then(u => u.user.isSuperuser || false);
    }),
    new SidebarItem(t`Resources`).children(
        new SidebarItem(t`Applications`, "/core/applications").activeWhen(
            `^/core/applications/(?<slug>${SLUG_REGEX})$`
        ),
        new SidebarItem(t`Sources`, "/core/sources").activeWhen(
            `^/core/sources/(?<slug>${SLUG_REGEX})$`,
        ),
        new SidebarItem(t`Providers`, "/core/providers").activeWhen(
            `^/core/providers/(?<id>${ID_REGEX})$`,
        ),
        new SidebarItem(t`Outposts`, "/outpost/outposts"),
        new SidebarItem(t`Outpost Service Connections`, "/outpost/service-connections"),
    ).when((): Promise<boolean> => {
        return me().then(u => u.user.isSuperuser || false);
    }),
    new SidebarItem(t`Events`).children(
        new SidebarItem(t`Logs`, "/events/log").activeWhen(
            `^/events/log/(?<id>${UUID_REGEX})$`
        ),
        new SidebarItem(t`Notification Rules`, "/events/rules"),
        new SidebarItem(t`Notification Transports`, "/events/transports"),
    ).when((): Promise<boolean> => {
        return me().then(u => u.user.isSuperuser || false);
    }),
    new SidebarItem(t`Customisation`).children(
        new SidebarItem(t`Policies`, "/policy/policies"),
        new SidebarItem(t`Property Mappings`, "/core/property-mappings"),
    ).when((): Promise<boolean> => {
        return me().then(u => u.user.isSuperuser || false);
    }),
    new SidebarItem(t`Flows`).children(
        new SidebarItem(t`Flows`, "/flow/flows").activeWhen(`^/flow/flows/(?<slug>${SLUG_REGEX})$`),
        new SidebarItem(t`Stages`, "/flow/stages"),
        new SidebarItem(t`Prompts`, "/flow/stages/prompts"),
        new SidebarItem(t`Invitations`, "/flow/stages/invitations"),
    ).when((): Promise<boolean> => {
        return me().then(u => u.user.isSuperuser || false);
    }),
    new SidebarItem(t`Identity & Cryptography`).children(
        new SidebarItem(t`Users`, "/identity/users").activeWhen(`^/identity/users/(?<id>${ID_REGEX})$`),
        new SidebarItem(t`Groups`, "/identity/groups"),
        new SidebarItem(t`Certificates`, "/crypto/certificates"),
        new SidebarItem(t`Tokens`, "/core/tokens"),
    ).when((): Promise<boolean> => {
        return me().then(u => u.user.isSuperuser || false);
    }),
];

@customElement("ak-interface-admin")
export class AdminInterface extends Interface {

    get sidebar(): SidebarItem[] {
        return SIDEBAR_ITEMS;
    }

}
