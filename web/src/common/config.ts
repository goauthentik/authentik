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
    pagination: {
        perPage: number;
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
    pagination = {
        perPage: 20,
    };
}

let globalUiConfig: Promise<UIConfig>;

export function uiConfig(): Promise<UIConfig> {
    if (!globalUiConfig) {
        globalUiConfig = me().then((user) => {
            const settings = user.user.settings;
            let config = new DefaultUIConfig();
            if (!settings) {
                return config;
            }
            if ("userInterface" in settings) {
                config = Object.assign(new DefaultUIConfig(), settings.userInterface);
            }
            return config;
        });
    }
    return globalUiConfig;
}
