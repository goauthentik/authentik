import { getCurrentScope, getTraceData } from "@sentry/core";

import { FetchParams, Middleware, RequestContext } from "@goauthentik/api";

export class SentryMiddleware implements Middleware {
    pre?(context: RequestContext): Promise<FetchParams | void> {
        if (getCurrentScope().getClient === undefined) {
            return Promise.resolve(context);
        }
        const traceData = getTraceData();
        // @ts-ignore
        context.init.headers["baggage"] = traceData["baggage"];
        // @ts-ignore
        context.init.headers["sentry-trace"] = traceData["sentry-trace"];
        return Promise.resolve(context);
    }
}
