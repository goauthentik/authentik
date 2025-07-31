/**
 * @file JSX runtime types for Lit.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

// /* eslint-disable @typescript-eslint/no-empty-object-type */

// /// <reference types="./lit-jsx-runtime.d.ts" />
// /**
//  * JSX runtime types for Lit.
//  */
// export namespace JSX {
//     // type ElementType = Lit.JSX.ElementType;
//     // interface Element extends Lit.JSX.Element {}
//     // interface ElementClass extends Lit.JSX.ElementClass {}
//     // interface ElementAttributesProperty extends Lit.JSX.ElementAttributesProperty {}
//     // interface ElementChildrenAttribute extends Lit.JSX.ElementChildrenAttribute {}
//     // type LibraryManagedAttributes<C, P> = Lit.JSX.LibraryManagedAttributes<C, P>;
//     // interface IntrinsicAttributes extends Lit.JSX.IntrinsicAttributes {}
//     // interface IntrinsicClassAttributes<T> extends Lit.JSX.IntrinsicClassAttributes<T> {}
//     interface IntrinsicElements extends Lit.JSX.IntrinsicElements {}
// }

import { JSX } from "./lit-jsx.js";

import { Attributes, ComponentChild, ComponentChildren, ComponentType, VNode } from "preact";

export { Fragment } from "preact";

export function jsx(
    type: string,
    props: JSX.HTMLAttributes &
        JSX.SVGAttributes &
        Record<string, any> & { children?: ComponentChild },
    key?: string,
): VNode<any>;
export function jsx<P>(
    type: ComponentType<P>,
    props: Attributes & P & { children?: ComponentChild },
    key?: string,
): VNode<any>;

export function jsxs(
    type: string,
    props: JSX.HTMLAttributes &
        JSX.SVGAttributes &
        Record<string, any> & { children?: ComponentChild[] },
    key?: string,
): VNode<any>;
export function jsxs<P>(
    type: ComponentType<P>,
    props: Attributes & P & { children?: ComponentChild[] },
    key?: string,
): VNode<any>;

export function jsxDEV(
    type: string,
    props: JSX.HTMLAttributes &
        JSX.SVGAttributes &
        Record<string, any> & { children?: ComponentChildren },
    key?: string,
): VNode<any>;
export function jsxDEV<P>(
    type: ComponentType<P>,
    props: Attributes & P & { children?: ComponentChildren },
    key?: string,
): VNode<any>;

// These are not expected to be used manually, but by a JSX transform
export function jsxTemplate(template: string[], ...expressions: any[]): VNode<any>;
export function jsxAttr(name: string, value: any): string | null;
export function jsxEscape<T>(value: T): string | null | VNode<any> | Array<string | null | VNode>;

export { JSX };
