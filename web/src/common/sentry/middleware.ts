import { getCurrentScope, getTraceData } from "@sentry/core";

import { FetchParams, Middleware, RequestContext } from "@goauthentik/api";

export class SentryMiddleware implements Middleware {
    pre?(context: RequestContext): Promise<FetchParams | void> {
        if (!getCurrentScope().getClient) {
            return Promise.resolve(context);
        }

        const traceData = getTraceData();

        context.init.headers = {
            ...context.init.headers,
            "baggage": traceData.baggage || "",
            "sentry-trace": traceData["sentry-trace"] || "",
        };

        return Promise.resolve(context);
    }
}
