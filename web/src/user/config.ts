import { me } from "../api/Users";

export enum UserDisplay {
    "username",
    "name",
    "email",
}

export interface UIConfig {
    enabledFeatures: {
        // API Request drawer in navbar
        apiDrawer: boolean;
        // Notification drawer in navbar
        notificationDrawer: boolean;
        // Settings in user dropdown
        settings: boolean;
        // Application edit in library (only shown when user is superuser)
        applicationEdit: boolean;
        // Search bar
        search: boolean;
    };
    navbar: {
        userDisplay: UserDisplay;
    };
    color: {
        background: string;
        cardBackground: string;
    };
}

export class DefaultUIConfig implements UIConfig {
    enabledFeatures = {
        apiDrawer: true,
        notificationDrawer: true,
        settings: true,
        applicationEdit: true,
        search: true,
    };
    navbar = {
        userDisplay: UserDisplay.username,
    };
    color = {
        background: "",
        cardBackground: "",
    };
}

export function parseConfig(raw: string): UIConfig {
    const c = JSON.parse(raw);
    return Object.assign(new DefaultUIConfig(), c);
}

export function uiConfig(): Promise<UIConfig> {
    return me().then((user) => {
        const settings = user.user.settings;
        let config = new DefaultUIConfig();
        if ("userInterface" in settings) {
            config = parseConfig(settings.userInterface);
        }
        console.debug(JSON.stringify(config));
        return config;
    });
}
