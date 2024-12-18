import { AKElement } from "@goauthentik/elements/Base";

import { TemplateResult, nothing } from "lit";
import { ReactiveControllerHost } from "lit";

export type ReactiveElementHost<T = AKElement> = Partial<ReactiveControllerHost> & T;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Constructor<T = object> = new (...args: any[]) => T;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type AbstractConstructor<T = object> = abstract new (...args: any[]) => T;

// authentik Search/List types
//
// authentik's list types (ak-dual-select, ak-list-select, ak-search-select) all take a tuple of two
// or three items, or a collection of groups of such tuples. In order to push dynamic checking
// around, we also allow the inclusion of a fourth component, which is just a scratchpad the
// developer can use for their own reasons.

// The displayed element for our list can be a TemplateResult. If it is, we *strongly* recommend
// that you include the `sortBy` string as well, which is used for sorting but is also used for our
// autocomplete element (ak-search-select) both for tracking the user's input and for what we
// display in the autocomplete input box.

// - key: string
// - label (string).  This is the field that will be sorted and used for filtering and searching.
// - desc (optional) A string or TemplateResult used to describe the option.
// - localMapping: The object the key represents; used by some specific apps. API layers may use
//   this as a way to find the referenced object, rather than the string and keeping a local map.
//
// Note that this is a *tuple*, not a record or map!

// prettier-ignore
export type SelectOption<T = never> = [
    key: string,
    label: string,
    desc?: string | TemplateResult,
    localMapping?: T,
];

/**
 * A search list without groups will always just consist of an array of SelectTuples and the
 * `grouped: false` flag. Note that it *is* possible to pass to any of the rendering components an
 * array of SelectTuples; they will be automatically mapped to a SelectFlat object.
 *
 */
/* PRIVATE */
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

export type SlottedTemplateResult = string | TemplateResult | typeof nothing;
export type Spread = { [key: string]: unknown };
