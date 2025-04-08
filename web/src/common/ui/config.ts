import { currentInterface } from "@goauthentik/common/sentry";
import { me } from "@goauthentik/common/users";

import { UiThemeEnum, UserSelf } from "@goauthentik/api";

export enum UserDisplay {
    username = "username",
    name = "name",
    email = "email",
}

export enum LayoutType {
    row = "row",
    column_2 = "2-column",
    column_3 = "3-column",
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
    theme: {
        base: UiThemeEnum;
        background: string;
        cardBackground: string;
    };
    pagination: {
        perPage: number;
    };
    layout: {
        type: LayoutType;
    };
    locale: string;
    defaults: {
        userPath: string;
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
    layout = {
        type: LayoutType.row,
    };
    navbar = {
        userDisplay: UserDisplay.username,
    };
    theme = {
        base: UiThemeEnum.Automatic,
        background: "",
        cardBackground: "",
    };
    pagination = {
        perPage: 20,
    };
    locale = "";
    defaults = {
        userPath: "users",
    };

    constructor() {
        if (currentInterface() === "user") {
            this.enabledFeatures.apiDrawer = false;
        }
    }
}

let globalUiConfig: Promise<UIConfig>;

export function getConfigForUser(user: UserSelf): UIConfig {
    const settings = user.settings;
    let config = new DefaultUIConfig();
    if (!settings) {
        return config;
    }
    config = Object.assign(new DefaultUIConfig(), settings);
    return config;
}

export function uiConfig(): Promise<UIConfig> {
    if (!globalUiConfig) {
        globalUiConfig = me().then((user) => {
            return getConfigForUser(user.user);
        });
    }
    return globalUiConfig;
}
