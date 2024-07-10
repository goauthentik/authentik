import { adminSettings } from "@goauthentik/components/oauth/settings";
import { UserManager } from "oidc-client-ts";

import { FetchParams, Middleware, RequestContext } from "@goauthentik/api";

export class TokenMiddleware implements Middleware {
    async pre?(context: RequestContext): Promise<FetchParams | void> {
        const user = await new UserManager(adminSettings).getUser();
        if (user !== null) {
            // @ts-ignore
            context.init.headers["Authorization"] = `Bearer ${user.access_token}`;
        }
        return Promise.resolve(context);
    }
}
