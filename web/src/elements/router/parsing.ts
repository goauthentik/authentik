import { ROUTE_SEPARATOR } from "#elements/router/constants";

export type PrimitiveRouteParameter = string | number | boolean | null | undefined;
export type RouteParameterRecord = Record<
    string,
    PrimitiveRouteParameter | PrimitiveRouteParameter[]
>;
export type RouterParameterInit = RouteParameterRecord | URLSearchParams;

//#region Serialization

function serialize(value: PrimitiveRouteParameter): string | null {
    if (!value) return null;

    if (typeof value === "boolean") {
        return value ? "true" : null;
    }

    return value.toString();
}

/**
 * Given a record of parameters, create a URLSearchParams object.
 */
export function recordToSearchParams(params: RouterParameterInit): URLSearchParams {
    if (params instanceof URLSearchParams) {
        return params;
    }

    const searchParams = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
        if (Array.isArray(value)) {
            for (const item of value) {
                const serialized = serialize(item);

                if (!serialized) continue;
                searchParams.append(key, serialized);
            }

            continue;
        }

        const serializedValue = serialize(value);
        if (!serializedValue) continue;

        searchParams.set(key, serializedValue);
    }

    return searchParams;
}

//#endregion

//#region Deserialization

function deserialize(value: string | null): PrimitiveRouteParameter | null {
    if (!value) return null;

    if (value === "true") {
        return true;
    }

    if (/^\d+$/.test(value)) {
        return parseInt(value, 10);
    }

    return value;
}

/**
 * Given a URLSearchParams object, create a record of parameters.
 *
 * Keys that appear multiple times in the search params will be mapped to an array of values.
 *
 * @param searchParams The URLSearchParams object to parse.
 */
export function searchParamsToRecord<T extends RouteParameterRecord = RouteParameterRecord>(
    searchParams: URLSearchParams,
): T {
    const params: Record<string, unknown> = {};

    for (const [key, value] of searchParams.entries()) {
        if (params[key]) {
            if (Array.isArray(params[key])) {
                params[key].push(deserialize(value));
            } else {
                params[key] = [params[key], deserialize(value)];
            }
        } else {
            params[key] = deserialize(value);
        }
    }

    return params as T;
}

//#endregion

//#region Decoding

export interface SerializedRoute {
    pathname: string;
    serializedParameters?: string;
}

export function pluckRoute(source: Pick<URL, "hash"> | string = window.location): SerializedRoute {
    source = typeof source === "string" ? new URL(source) : source;

    const [pathname, serializedParameters] = source.hash.slice(1).split(ROUTE_SEPARATOR, 2);

    return {
        pathname,
        serializedParameters,
    };
}

export function decodeParameters<T extends RouteParameterRecord = RouteParameterRecord>(
    source: Pick<URL, "hash"> = window.location,
): Partial<T> {
    if (!source.hash.includes(ROUTE_SEPARATOR)) {
        return {};
    }

    const { serializedParameters } = pluckRoute(source);

    if (!serializedParameters) {
        return {};
    }

    if (serializedParameters.startsWith("%7B")) {
        try {
            return JSON.parse(decodeURIComponent(serializedParameters));
        } catch {
            return {};
        }
    }

    return searchParamsToRecord<T>(new URLSearchParams(serializedParameters));
}
