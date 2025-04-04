import { me } from "@goauthentik/common/users";
import { isUserRoute } from "@goauthentik/elements/router";

import { UiThemeEnum } from "@goauthentik/api";

export enum UserDisplay {
    username = "username",
    name = "name",
    email = "email",
    none = "none",
}

export enum LayoutType {
    row = "row",
    column_2 = "2-column",
    column_3 = "3-column",
}

export interface UIConfig {
    enabledFeatures: {
        /**
         * Whether to show the API request drawer in the navbar.
         */
        apiDrawer: boolean;
        /**
         * Whether to show the notification drawer in the navbar.
         */
        notificationDrawer: boolean;
        /**
         * Whether to show the settings in the user dropdown.
         */
        settings: boolean;
        /**
         * Whether to show the application edit button in the library.
         *
         * This is only shown when the user is a superuser.
         */
        applicationEdit: boolean;
        /**
         * Whether to show the search bar.
         */
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
        /**
         * Number of items to show per page in paginated lists.
         */
        perPage: number;
    };
    layout: {
        /**
         * Layout type to use for the application.
         */
        type: LayoutType;
    };
    /**
     * Locale to use for the application.
     */
    locale: string;
    /**
     * Default values.
     */
    defaults: {
        /**
         * Default path to use for user API calls.
         */
        userPath: string;
    };
}

export function createUIConfig(overrides: Partial<UIConfig> = {}): UIConfig {
    const uiConfig: UIConfig = {
        enabledFeatures: {
            // TODO: Is the intent that only user routes should have the API drawer disabled,
            // or only admin routes?
            apiDrawer: !isUserRoute(),
            notificationDrawer: true,
            settings: true,
            applicationEdit: true,
            search: true,
        },
        layout: {
            type: LayoutType.row,
        },
        navbar: {
            userDisplay: UserDisplay.username,
        },
        theme: {
            base: UiThemeEnum.Automatic,
            background: "",
            cardBackground: "",
        },
        pagination: {
            perPage: 20,
        },
        locale: "",
        defaults: {
            userPath: "users",
        },
    };

    // TODO: Should we deep merge the overrides instead of shallow?
    Object.assign(uiConfig, overrides);

    return uiConfig;
}

let cachedUIConfig: UIConfig | null = null;

export function uiConfig(): Promise<UIConfig> {
    if (cachedUIConfig) return Promise.resolve(cachedUIConfig);

    return me().then((session) => {
        cachedUIConfig = createUIConfig(session.user.settings);

        return cachedUIConfig;
    });
}
