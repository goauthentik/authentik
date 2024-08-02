import { TemplateResult } from "lit";

// - key: string
// - label (string or TemplateResult),
// - sortBy (optional) string to sort by. If the sort string is not supplied, the toString()
//   form of the label, either as a string or the html of TemplateResult, will be used.
// - localMapping: The object the key represents; used by some specific apps. API layers may use
//   this as a way to find the referenced object, rather than the string and keeping a local map.
//
// Note that this is a *tuple*, not a record or map!

export type SelectOption<T = never> = [
    key: string,
    label: string | TemplateResult,
    sortBy?: string,
    localMapping?: T,
];

/**
 * A search list without groups will always just consist of an array of SelectTuples and the
 * `grouped: false` flag. Note that it *is* possible to pass to any of the rendering components an
 * array of SelectTuples; they will be automatically mapped to a SelectFlat object.
 *
 */
export type SelectFlat<T = never> = {
    grouped: false;
    options: SelectOption<T>[];
};

/**
 * A search group consists of a group name and a collection of SelectTuples.
 *
 */
export type SelectGroup<T = never> = { name: string; options: SelectOption<T>[] };

/**
 * A grouped search is an array of SelectGroups, of course!
 *
 */
export type SelectGrouped<T = never> = {
    grouped: true;
    options: SelectGroup<T>[];
};

/**
 * Internally, we only work with these two, but we have the `SelectOptions` variant
 * below to support the case where you just want to pass in an array of SelectTuples.
 *
 */
export type GroupedOptions<T = never> = SelectGrouped<T> | SelectFlat<T>;
export type SelectOptions<T = never> = SelectOption<T>[] | GroupedOptions<T>;
