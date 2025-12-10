import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";

import { Middleware, ResponseContext } from "@goauthentik/api";

import { msg } from "@lit/localize";

export class MessageMiddleware implements Middleware {
    post(context: ResponseContext): Promise<Response | void> {
        if (context.response.status >= 500) {
            showMessage({
                level: MessageLevel.error,
                message: msg("API request failed"),
                description: `${context.init.method} ${context.url}: ${context.response.status}`,
            });
        }
        return Promise.resolve(context.response);
    }
}
