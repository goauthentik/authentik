import { SentryIgnoredError } from "#common/sentry/error";

export class PreventFormSubmit extends SentryIgnoredError {
    // Stub class which can be returned by form elements to prevent the form from submitting
    constructor(
        public message: string,
        public element?: Element,
    ) {
        super();
    }
}
