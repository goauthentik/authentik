/**
 * @file Common types for routing.
 */

export type PrimitiveRouteParameter = string | number | boolean | null | undefined;
export type RouteParameterRecord = { [key: string]: PrimitiveRouteParameter };
