import { UIConfig } from "#common/ui/config";

import { SessionUser } from "@goauthentik/api";

export interface PageHeaderInit {
    header: string | null;
    description?: string | null;
    icon?: string | null;
    iconImage?: boolean;
}

export interface NavbarRenderProps extends Pick<PageHeaderInit, "description" | "icon"> {
    open: boolean; // Is the sidebar visible?
    logo: string; // URL to the brand logo
    onClick: () => void; // action taken when the navigation button is clicked
    title: string; // Title of the current page
    iconIsImage: boolean; // The icon is a URL to an image, not a font-style reference
    base: string; // base URL of the admin interface
    session?: SessionUser; // User details needed by the toolbar
    uiConfig?: UIConfig; // UI Details needed by the toolbar
}
