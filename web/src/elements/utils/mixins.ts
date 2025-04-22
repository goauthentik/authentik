/**
 * @file Mixin utilities for Lit elements.
 */
import type { LitElement } from "lit";

export type AbstractLitElementConstructor = abstract new (...args: never[]) => LitElement;

export type LitElementConstructor = new (...args: never[]) => LitElement;

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
export interface CreateMixinInit<T extends LitElementConstructor = LitElementConstructor> {
    /**
     * The superclass constructor to extend.
     */
    SuperClass: T;
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
export function createMixin<Mixin>(mixinCallback: (init: CreateMixinInit) => unknown) {
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
            SuperClass: SuperClass as LitElementConstructor,
            subscribe,
        });

        return MixinClass as ConstructorWithMixin<T, Mixin>;
    };
}
