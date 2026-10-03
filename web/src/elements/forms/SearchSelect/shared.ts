import type { SlottedTemplateResult } from "#elements/types";

/**
 * Where a search select gets its objects, and how it presents them.
 *
 * @template T The API object the select chooses between.
 */
export interface SearchSelectSource<T> {
    /**
     * Fetch the objects matching a query, or the default page without one.
     */
    fetchObjects(query?: string): Promise<T[]>;

    /**
     * The key identifying an object, which is also the select's form value.
     */
    keyOf(object: T): string;

    /**
     * The label shown for an object, in the input and in its option.
     */
    labelOf(object: T): string;

    /**
     * A secondary line shown under an option's label.
     */
    describe?(object: T): SlottedTemplateResult;

    /**
     * Whether an object is listed but cannot be chosen. Pair with `describe` to say why.
     */
    isDisabled?(object: T): boolean;

    /**
     * Split the objects into named groups. An empty name leaves a group untitled.
     */
    groupBy?(objects: T[]): [name: string, objects: T[]][];

    /**
     * Choose an object when the select has no value once its first fetch lands,
     * e.g. a default flow picked by slug.
     */
    preselect?(objects: T[]): T | undefined;
}

/**
 * Add `search` to API list arguments when a query is present.
 */
export function withQuery<T extends object>(search: string | undefined, args: T): T {
    return search ? { ...args, search } : args;
}

/**
 * An element ID for an option, safe to reference from `aria-activedescendant`.
 */
export function formatOptionID(key: string): string {
    return `option-${key.replace(/\s+/g, "_")}`;
}
