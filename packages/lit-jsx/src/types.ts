import type { nothing, TemplateResult } from "lit";
import type { DirectiveResult } from "lit/directive.js";

/**
 * A convenience type representing the result of a slotted template.
 *
 * Copied from `web/src/elements/types.ts`; `web/` re-exports from here once it
 * adopts this package (see the design spec's migration plan).
 */
export type SlottedTemplateResult =
    | string
    | TemplateResult
    | typeof nothing
    | null
    | DirectiveResult
    | HTMLElement;

/**
 * Type utility to make readonly properties mutable.
 */
export type Writeable<T> = { -readonly [P in keyof T]: T[P] };

/**
 * Utility type to compare if two types are equal.
 */
export type IfEquals<X, Y, A = X, B = never> =
    (<T>() => T extends X ? 1 : 2) extends <T>() => T extends Y ? 1 : 2 ? A : B;

/**
 * Utility type to get the writable keys of an object.
 */
export type WritableKeys<T> = {
    [K in keyof T]-?: IfEquals<{ [Q in K]: T[K] }, { -readonly [Q in K]: T[K] }, K, never>;
}[keyof T];

/**
 * Utility type to get the keys of an object that are not in the base type.
 */
export type OwnKeys<Target, Base> = Exclude<keyof Target, keyof Base>;

/**
 * Utility type to represent the writable properties of an object that are not
 * in the base type.
 */
export type OwnPropertyRecord<Target, Base> = {
    [K in OwnKeys<Target, Base> as K extends WritableKeys<Target> ? K : never]: Target[K];
};
