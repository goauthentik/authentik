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
    };
    navbar: {
        userDisplay: "username" | "name" | "email";
    };
}

export const DefaultUIConfig: UIConfig = {
    enabledFeatures: {
        apiDrawer: true,
        notificationDrawer: true,
        settings: true,
        applicationEdit: true,
    },
    navbar: {
        userDisplay: "name",
    },
};

export function uiConfig(): Promise<UIConfig> {
    return Promise.resolve(DefaultUIConfig);
}
