/**
 * @file Common types for routing.
 */

import { DefaultImportCallback, ImportCallback } from "#common/modules/types";

import { SlottedTemplateResult } from "#elements/types";

export type PrimitiveRouteParameter = string | number | boolean | null | undefined;
export type RouteParameterRecord = { [key: string]: PrimitiveRouteParameter };

export type RouteParameters = Record<string, string>;

export type RouteLoader = DefaultImportCallback<CustomElementConstructor>;

export type RouteHandler<P extends object = RouteParameters> = (
    parameters: P,
) => SlottedTemplateResult;

export interface RouteInit<P extends object = RouteParameters> {
    pattern: RegExp | string;
    loader?: RouteLoader | ImportCallback<object>;
    handler?: RouteHandler<P>;
}

export type RouteEntry =
    | [pattern: RegExp | string, loader: ImportCallback<object>, handler: RouteHandler]
    | [pattern: RegExp | string, loader: RouteLoader, handler?: RouteHandler];
type RouteGroup = [prefix: string, children: NestedRouteEntry[]];
type NestedRouteEntry = RouteEntry | RouteGroup;

export function collateRoutes(entries: NestedRouteEntry[], prefix = ""): RouteEntry[] {
    return entries.flatMap((entry) => {
        const [segment, second] = entry;
        if (Array.isArray(second)) {
            return collateRoutes(second, `${prefix}/${segment}`);
        }
        return [[`${prefix}/${segment}`, ...entry.slice(1)] as RouteEntry];
    });
}
