import { customElement } from "lit-element";
import { User } from "../api/user";
import { SidebarItem } from "../elements/sidebar/Sidebar";
import { SLUG_REGEX } from "../elements/router/Route";
import { Interface } from "./Interface";

export const SIDEBAR_ITEMS: SidebarItem[] = [
    new SidebarItem("Library", "/library/"),
    new SidebarItem("Monitor", "/events/log").when((): Promise<boolean> => {
        return User.me().then(u => u.is_superuser);
    }),
    new SidebarItem("Administration").children(
        new SidebarItem("Overview", "/administration/overview-ng/"),
        new SidebarItem("System Tasks", "/administration/tasks/"),
        new SidebarItem("Applications", "/administration/applications/").activeWhen(
            `^/applications/(?<slug>${SLUG_REGEX})/$`
        ),
        new SidebarItem("Sources", "/administration/sources/").activeWhen(
            `^/sources/(?<slug>${SLUG_REGEX})/$`,
        ),
        new SidebarItem("Providers", "/administration/providers/"),
        new SidebarItem("Flows").children(
            new SidebarItem("Flows", "/administration/flows/").activeWhen(`^/flows/(?<slug>${SLUG_REGEX})/$`),
            new SidebarItem("Stages", "/administration/stages/"),
            new SidebarItem("Prompts", "/administration/stages/prompts/"),
            new SidebarItem("Invitations", "/administration/stages/invitations/"),
        ),
        new SidebarItem("User Management").children(
            new SidebarItem("User", "/administration/users/"),
            new SidebarItem("Groups", "/administration/groups/")
        ),
        new SidebarItem("Outposts").children(
            new SidebarItem("Outposts", "/administration/outposts/"),
            new SidebarItem("Service Connections", "/administration/outposts/service_connections/")
        ),
        new SidebarItem("Policies", "/administration/policies/"),
        new SidebarItem("Property Mappings", "/administration/property-mappings"),
        new SidebarItem("Certificates", "/administration/crypto/certificates"),
        new SidebarItem("Tokens", "/administration/tokens/"),
    ).when((): Promise<boolean> => {
        return User.me().then(u => u.is_superuser);
    })
];

@customElement("ak-interface-admin")
export class AdminInterface extends Interface {

    get sidebar(): SidebarItem[] {
        return SIDEBAR_ITEMS;
    }

}
