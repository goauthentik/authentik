import { UIConfig } from "#common/ui/config";

import { SessionUser } from "@goauthentik/api";

export interface NavbarRenderProps {
    open: boolean; // Is the sidebar visible?
    logo: string; // URL to the brand logo
    onClick: () => void; // action taken when the navigation button is clicked
    title: string; // Title of the current page
    description?: string; // Subtitle of the current page, if any
    icon?: string; // The icon for the curent page, if any
    iconIsImage: boolean; // The icon is a URL to an image, not a font-style reference
    base: string; // base URL of the admin interface
    session?: SessionUser; // User details needed by the toolbar
    uiConfig?: UIConfig; // UI Details needed by the toolbar
}

export interface PageHeaderInit {
    header?: string;
    description?: string;
    icon?: string;
    iconImage?: boolean;
}
