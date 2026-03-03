import { isLaunchUrlValid } from "#common/utils";

import type { Application } from "@goauthentik/api";

export const appHasLaunchUrl = (app: Application) => {
    const url = app.launchUrl;
    return isLaunchUrlValid(url);
};
