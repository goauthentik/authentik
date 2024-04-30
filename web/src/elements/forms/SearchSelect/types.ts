import type { TemplateResult } from "lit";

/* key, label, description */
export type SearchTuple = [string, string, undefined | string | TemplateResult];
export type SearchGroup = { name: string; options: SearchTuple[] };
export type SearchGrouped = {
    grouped: true;
    options: SearchGroup[];
};

export type SearchFlat = {
    grouped: false;
    options: SearchTuple[];
};

export type GroupedOptions = SearchGrouped | SearchFlat;

export type SearchOptions = SearchTuple[] | GroupedOptions;

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
