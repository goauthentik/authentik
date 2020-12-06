import { customElement } from "lit-element";
import { User } from "../api/user";
import { SidebarItem } from "../elements/sidebar/Sidebar";
import { Interface } from "./Interface";

export const SIDEBAR_ITEMS: SidebarItem[] = [
    {
        name: "Library",
        path: ["/library/"],
    },
    {
        name: "Monitor",
        path: ["/audit/audit/"],
        condition: (): Promise<boolean> => {
            return User.me().then(u => u.is_superuser);
        },
    },
    {
        name: "Administration",
        children: [
            {
                name: "Overview",
                path: ["/administration/overview-ng/"],
            },
            {
                name: "System Tasks",
                path: ["/administration/tasks/"],
            },
            {
                name: "Applications",
                path: ["/administration/applications/"],
            },
            {
                name: "Sources",
                path: ["/administration/sources/"],
            },
            {
                name: "Providers",
                path: ["/administration/providers/"],
            },
            {
                name: "User Management",
                children: [
                    {
                        name: "User",
                        path: ["/administration/users/"],
                    },
                    {
                        name: "Groups",
                        path: ["/administration/groups/"],
                    },
                ],
            },
            {
                name: "Outposts",
                children: [
                    {
                        name: "Outposts",
                        path: ["/administration/outposts/"],
                    },
                    {
                        name: "Service Connections",
                        path: ["/administration/outposts/service_connections/"],
                    },
                ],
            },
            {
                name: "Policies",
                path: ["/administration/policies/"],
            },
            {
                name: "Property Mappings",
                path: ["/administration/property-mappings/"],
            },
            {
                name: "Flows",
                children: [
                    {
                        name: "Flows",
                        path: ["/administration/flows/"],
                    },
                    {
                        name: "Stages",
                        path: ["/administration/stages/"],
                    },
                    {
                        name: "Prompts",
                        path: ["/administration/stages/prompts/"],
                    },
                    {
                        name: "Invitations",
                        path: ["/administration/stages/invitations/"],
                    },
                ],
            },
            {
                name: "Certificates",
                path: ["/administration/crypto/certificates/"],
            },
            {
                name: "Tokens",
                path: ["/administration/tokens/"],
            },
        ],
        condition: (): Promise<boolean> => {
            return User.me().then(u => u.is_superuser);
        },
    },
];

@customElement("ak-interface-admin")
export class AdminInterface extends Interface {

    get sidebar(): SidebarItem[] {
        return SIDEBAR_ITEMS;
    }

}
