import { HorizontalFormElement } from "@goauthentik/app/elements/forms/HorizontalFormElement";

export class PreventFormSubmit {
    // Stub class which can be returned by form elements to prevent the form from submitting
    constructor(
        public message: string,
        public element?: HorizontalFormElement,
    ) {}
}
