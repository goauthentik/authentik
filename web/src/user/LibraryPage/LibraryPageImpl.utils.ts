import type { Application } from "@goauthentik/api";
import { isLaunchUrlValid } from "#common/utils";

export const appHasLaunchUrl = (app: Application) => {
    const url = app.launchUrl;
    return isLaunchUrlValid(url)
};
