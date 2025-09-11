import { OwnPropertyRecord, Writeable } from "#common/types";

import type { LitElement, nothing, ReactiveControllerHost, TemplateResult } from "lit";

//#region HTML Helpers

/**
 * Utility type to extract a record of tag names which correspond to a given type.
 *
 * This is useful when selecting a subset of elements that share a common base class.
 */
export type HTMLElementTagNameMapOf<T> = {
    [K in keyof HTMLElementTagNameMap as HTMLElementTagNameMap[K] extends T
        ? K
        : never]: HTMLElementTagNameMap[K];
};

//#endregion

//#region Element Properties

/**
 *
 * Given an element and a base class, pluck the properties not defined on the base class.
 */
export type TemplatedProperties<
    T extends HTMLElement,
    Base extends Element = HTMLElement,
> = Partial<OwnPropertyRecord<T, Base>>;

/**
 * Given a record-like object, prefixes each key with a dot, allowing it to be spread into a
 * template literal.
 *
 * ```ts
 * interface MyElementProperties {
 *     foo: string;
 *     bar: number;
 * }
 *
 * const properties {} as LitPropertyRecord<MyElementProperties>
 *
 * console.log(properties) // { '.foo': string; '.bar': number }
 * ```
 */
export type LitPropertyRecord<T extends object> = {
    [K in keyof T as K extends string ? LitPropertyKey<K> : never]?: T[K];
};

/**
 * A type that represents a property key that can be used in a LitPropertyRecord.
 *
 * @see {@linkcode LitPropertyRecord}
 */
export type LitPropertyKey<K> = K extends string ? `.${K}` | `?${K}` | K : K;

/**
 * A React-like functional component. Used to render a component in a template.
 *
 * @template P The type of the props object.
 * @param props The props object.
 * @param children The children to render.
 * @returns The rendered template.
 */
export type LitFC<P> = (
    props: P,
    children?: SlottedTemplateResult,
) => SlottedTemplateResult | SlottedTemplateResult[];

//#endregion

//#region Host/Controller

/**
 * A custom element which may be used as a host for a ReactiveController.
 *
 * @remarks
 *
 * This type is derived from an internal type in Lit.
 */
export type ReactiveElementHost<T> = Partial<ReactiveControllerHost & Writeable<T>> & HTMLElement;

//#endregion

//#region Constructors

export type AbstractLitElementConstructor<T = unknown> = abstract new (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ...args: any[]
) => LitElement & T;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type LitElementConstructor<T = unknown> = new (...args: any[]) => LitElement & T;

//#endregion

//#region Mixins

/**
 * A constructor that has been extended with a mixin.
 */
export type ConstructorWithMixin<SuperClass, Mixin> =
    // Is the superclass abstract?
    SuperClass extends abstract new (...args: never[]) => unknown
        ? // Lift the abstractness to of the mixin.
          new (...args: ConstructorParameters<SuperClass>) => InstanceType<SuperClass> & Mixin
        : // Is the superclass **not** abstract?
          SuperClass extends new (...args: never[]) => unknown
          ? // So shall be the mixin.
            new (...args: ConstructorParameters<SuperClass>) => InstanceType<SuperClass> & Mixin
          : never;

/**
 * The init object passed to the `createMixin` callback.
 */
export interface CreateMixinInit<C = unknown> {
    /**
     * The superclass constructor to extend.
     */
    SuperClass: LitElementConstructor<C>;
    /**
     * Whether or not to subscribe to the context.
     *
     * Should the context be explicitly reset, all active web components that are
     * currently active and subscribed to the context will automatically have a `requestUpdate()`
     * triggered with the new configuration.
     */
    subscribe?: boolean;
}

/**
 * Create a mixin for a LitElement.
 *
 * @param mixinCallback The callback that will be called to create the mixin.
 * @template Mixin The mixin class to union with the superclass.
 */
export function createMixin<Mixin, C = unknown>(
    mixinCallback: (init: CreateMixinInit<C>) => unknown,
) {
    return <T extends LitElementConstructor | AbstractLitElementConstructor>(
        /**
         * The superclass constructor to extend.
         */ SuperClass: T,
        /**
         * Whether or not to subscribe to the context.
         *
         * Should the context be explicitly reset, all active web components that are
         * currently active and subscribed to the context will automatically have a `requestUpdate()`
         * triggered with the new configuration.
         */
        subscribe?: boolean,
    ) => {
        const MixinClass = mixinCallback({
            SuperClass: SuperClass as LitElementConstructor<C>,
            subscribe,
        });

        return MixinClass as ConstructorWithMixin<T, Mixin>;
    };
}

//#region Search/List types

/**
 * authentik's list types (ak-dual-select, ak-list-select, ak-search-select) all take a tuple of two
 * or three items, or a collection of groups of such tuples. In order to push dynamic checking
 * around, we also allow the inclusion of a fourth component, which is just a scratchpad the
 * developer can use for their own reasons.
 *
 * The displayed element for our list can be a TemplateResult.
 *
 * If it is, we *strongly* recommend that you include the `sortBy` string as well, which is used for sorting but is also used for our autocomplete element (ak-search-select),
 * both for tracking the user's input and for what we display in the autocomplete input box.
 *
 * Note that this is a *tuple*, not a record or map!
 */
export type SelectOption<T = never> = [
    /**
     * The key that will be used for sorting and filtering.
     */
    key: string,
    /**
     * The field that will be sorted and used for filtering and searching.
     */
    label: string,
    /**
     * A string or TemplateResult used to describe the option.
     */
    desc?: string | TemplateResult,
    /**
     * The object the key represents; used by some specific apps. API layers may use
     *   this as a way to find the referenced object, rather than the string and keeping a local map.
     */
    localMapping?: T,
];

/**
 * A search list without groups will always just consist of an array of SelectTuples and the
 * `grouped: false` flag. Note that it *is* possible to pass to any of the rendering components an
 * array of SelectTuples; they will be automatically mapped to a SelectFlat object.
 *
 * @internal
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

//#endregion

/**
 * A convenience type representing the result of a slotted template, i.e.
 *
 * - A string, which will be rendered as text.
 * - A TemplateResult, which will be rendered as HTML.
 * - `nothing`, which will not be rendered.
 */
export type SlottedTemplateResult = string | TemplateResult | typeof nothing;
export type Spread = { [key: string]: unknown };
