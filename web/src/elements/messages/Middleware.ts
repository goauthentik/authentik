import { Middleware, ResponseContext } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { MessageLevel } from "./Message";
import { showMessage } from "./MessageContainer";

export class MessageMiddleware implements Middleware {
    post(context: ResponseContext): Promise<Response | void> {
        if (context.response.status >= 500) {
            showMessage({
                level: MessageLevel.error,
                message: t`API request failed`,
                description: `${context.init.method} ${context.url}: ${context.response.status}`,
            });
        }
        return Promise.resolve(context.response);
    }
}
