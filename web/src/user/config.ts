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
        userDisplay: "username" | "name" | "email";
    };
    color: {
        background: string;
        cardBackground: string;
    };
}

export const DefaultUIConfig: UIConfig = {
    enabledFeatures: {
        apiDrawer: true,
        notificationDrawer: true,
        settings: true,
        applicationEdit: true,
        search: true,
    },
    navbar: {
        userDisplay: "name",
    },
    color: {
        background: "",
        cardBackground: "",
    },
};

export function uiConfig(): Promise<UIConfig> {
    return Promise.resolve(DefaultUIConfig);
}
