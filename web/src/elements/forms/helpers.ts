import { HorizontalFormElement } from "#elements/forms/HorizontalFormElement";

export class PreventFormSubmit {
    // Stub class which can be returned by form elements to prevent the form from submitting
    public constructor(
        public message: string,
        public element?: HorizontalFormElement,
    ) {}
}
