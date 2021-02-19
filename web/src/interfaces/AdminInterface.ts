import { customElement } from "lit-element";
import { User } from "../api/Users";
import { SidebarItem } from "../elements/sidebar/Sidebar";
import { SLUG_REGEX } from "../elements/router/Route";
import { Interface } from "./Interface";

export const SIDEBAR_ITEMS: SidebarItem[] = [
    new SidebarItem("Library", "/library"),
    new SidebarItem("Monitor").children(
        new SidebarItem("Overview", "/administration/overview"),
        new SidebarItem("System Tasks", "/administration/system-tasks"),
    ).when((): Promise<boolean> => {
        return User.me().then(u => u.is_superuser);
    }),
    new SidebarItem("Events").children(
        new SidebarItem("Log", "/events/log"),
        new SidebarItem("Notification Rules", "/events/rules"),
        new SidebarItem("Notification Transports", "/events/transports"),
    ).when((): Promise<boolean> => {
        return User.me().then(u => u.is_superuser);
    }),
    new SidebarItem("Resources").children(
        new SidebarItem("Applications", "/applications").activeWhen(
            `^/applications/(?<slug>${SLUG_REGEX})$`
        ),
        new SidebarItem("Sources", "/sources").activeWhen(
            `^/sources/(?<slug>${SLUG_REGEX})$`,
        ),
        new SidebarItem("Providers", "/providers"),
        new SidebarItem("Outposts", "/outposts"),
        new SidebarItem("Outpost Service Connections", "/outpost-service-connections"),
    ).when((): Promise<boolean> => {
        return User.me().then(u => u.is_superuser);
    }),
    new SidebarItem("Customisation").children(
        new SidebarItem("Policies", "/policies"),
        new SidebarItem("Property Mappings", "/property-mappings"),
    ).when((): Promise<boolean> => {
        return User.me().then(u => u.is_superuser);
    }),
    new SidebarItem("Flows").children(
        new SidebarItem("Flows", "/flows").activeWhen(`^/flows/(?<slug>${SLUG_REGEX})$`),
        new SidebarItem("Stages", "/administration/stages/"),
        new SidebarItem("Prompts", "/administration/stages_prompts/"),
        new SidebarItem("Invitations", "/administration/stages/invitations/"),
    ).when((): Promise<boolean> => {
        return User.me().then(u => u.is_superuser);
    }),
    new SidebarItem("Identity & Cryptography").children(
        new SidebarItem("User", "/users"),
        new SidebarItem("Groups", "/groups"),
        new SidebarItem("Certificates", "/crypto/certificates"),
        new SidebarItem("Tokens", "/administration/tokens/"),
    ).when((): Promise<boolean> => {
        return User.me().then(u => u.is_superuser);
    }),
];

@customElement("ak-interface-admin")
export class AdminInterface extends Interface {

    get sidebar(): SidebarItem[] {
        return SIDEBAR_ITEMS;
    }

}
