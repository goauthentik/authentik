import * as Sentry from "@sentry/react";
import { Integrations } from "@sentry/tracing";

Sentry.init({
    dsn: "https://339d36db58e6476aa0430aaff4e0610c@sentry.beryju.org/9",
    integrations: [new Integrations.BrowserTracing()],
    tracesSampleRate: 0.6,
});
