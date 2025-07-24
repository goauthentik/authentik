import { ifDefined } from "lit/directives/if-defined.js";

// A variant of `ifDefined` that also doesn't do anything if the string is empty.
export const ifNotEmpty = <T>(value: T) =>
    ifDefined(value === "" ? undefined : (value ?? undefined));
