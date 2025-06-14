import type { TemplateResult } from "lit";

/**
 * A search tuple consists of a [key, label, description]
 * The description is optional.  The key must always be a string.
 *
 */
export type SearchTuple = [
    key: string,
    label: string,
    description: undefined | string | TemplateResult,
];

/**
 * A search list without groups will always just consist of an array of SearchTuples and the
 * `grouped: false` flag. Note that it *is* possible to pass to any of the rendering components an
 * array of SearchTuples; they will be automatically mapped to a SearchFlat object.
 *
 */
export type SearchFlat = {
    grouped: false;
    options: SearchTuple[];
};

/**
 * A search group consists of a group name and a collection of SearchTuples.
 *
 */
export type SearchGroup = { name: string; options: SearchTuple[] };

/**
 * A grouped search is an array of SearchGroups, of course!
 *
 */
export type SearchGrouped = {
    grouped: true;
    options: SearchGroup[];
};

/**
 * Internally, we only work with these two, but we have the `SearchOptions` variant
 * below to support the case where you just want to pass in an array of SearchTuples.
 *
 */
export type GroupedOptions = SearchGrouped | SearchFlat;
export type SearchOptions = SearchTuple[] | GroupedOptions;

// These can safely be ignored for now.
export type Group<T> = [string, T[]];

export type ElementRendererBase<T> = (element: T) => string;
export type ElementRenderer<T, S = keyof T> = ElementRendererBase<T> | S;

export type DescriptionRendererBase<T> = (element: T) => TemplateResult | string;
export type DescriptionRenderer<T, S = keyof T> = ElementRendererBase<T> | S;

export type ValueExtractorBase<T> = (element: T | undefined) => keyof T | undefined;
export type ValueExtractor<T, S = keyof T> = ValueExtractorBase<T> | S;

export type ValueSelectorBase<T> = (element: T, elements: T[]) => boolean;
export type ValueSelector<T, S extends keyof T> = S extends S
    ? ValueSelectorBase<T> | [T, T[S]]
    : never;

export type GroupByBase<T> = (elements: T[]) => Group<T>[];
export type GroupBy<T, S = keyof T> = GroupByBase<T> | keyof S;
