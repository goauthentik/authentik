/**
 * Various utilities for JSON References *(http://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03)* and
 * JSON Pointers *(https://tools.ietf.org/html/rfc6901)*.
 */
declare module 'json-refs' {
    /**
     * Clears the internal cache of remote documents, reference details, etc.
     */
    export function clearCache(): void;

    /**
     * Takes an array of path segments and decodes the JSON Pointer tokens in them.
     * @param path - The array of path segments
     * @returns the array of path segments with their JSON Pointer tokens decoded
     * @throws if the path is not an `Array`
     * @see
     */
    export function decodePath(path: string[]): string[];

    /**
     * Takes an array of path segments and encodes the special JSON Pointer characters in them.
     * @param path - The array of path segments
     * @returns the array of path segments with their JSON Pointer tokens encoded
     * @throws if the path is not an `Array`
     * @see
     */
    export function encodePath(path: string[]): string[];

    /**
     * Finds JSON References defined within the provided array/object.
     * @param obj - The structure to find JSON References within
     * @param options - The JsonRefs options
     * @returns an object whose keys are JSON Pointers
     *          *(fragment version)* to where the JSON Reference is defined and whose values are {@link UnresolvedRefDetails}.
     * @throws when the input arguments fail validation or if `options.subDocPath` points to an invalid location
     */
    export function findRefs(obj: any[] | object, options?: JsonRefsOptions): { [key: string]: (UnresolvedRefDetails|undefined) };

    /**
     * Finds JSON References defined within the document at the provided location.
     * 
     * This API is identical to {@link findRefs} except this API will retrieve a remote document and then
     * return the result of {@link findRefs} on the retrieved document.
     * @param location - The location to retrieve *(Can be relative or absolute, just make sure you look at the
     *        {@link JsonRefsOptions|options documentation} to see how relative references are handled.)*
     * @param options - The JsonRefs options
     * @returns a promise that resolves a
     *          {@link RetrievedRefsResults} and rejects with an `Error` when the input arguments fail validation,
     *          when `options.subDocPath` points to an invalid location or when the location argument points to an unloadable
     *          resource
     */
    export function findRefsAt(location: string, options?: JsonRefsOptions): Promise<RetrievedRefsResults>;

    /**
     * Returns detailed information about the JSON Reference.
     * @param obj - The JSON Reference definition
     * @returns the detailed information
     */
    export function getRefDetails(obj: object): UnresolvedRefDetails;

    /**
     * Returns whether the argument represents a JSON Pointer.
     * 
     * A string is a JSON Pointer if the following are all true:
     * 
     * * The string is of type `String`
     * * The string must be empty, `#` or start with a `/` or `#/`
     * @param ptr - The string to check
     * @param throwWithDetails - Whether or not to throw an `Error` with the details as to why the value
     *        provided is invalid
     * @returns the result of the check
     * @throws when the provided value is invalid and the `throwWithDetails` argument is `true`
     * @see
     */
    export function isPtr(ptr: string, throwWithDetails?: boolean): boolean;

    /**
     * Returns whether the argument represents a JSON Reference.
     * 
     * An object is a JSON Reference only if the following are all true:
     * 
     * * The object is of type `Object`
     * * The object has a `$ref` property
     * * The `$ref` property is a valid URI *(We do not require 100% strict URIs and will handle unescaped special
     * characters.)*
     * @param obj - The object to check
     * @param throwWithDetails - Whether or not to throw an `Error` with the details as to why the value
     *        provided is invalid
     * @returns the result of the check
     * @throws when the provided value is invalid and the `throwWithDetails` argument is `true`
     * @see
     */
    export function isRef(obj: object, throwWithDetails?: boolean): boolean;

    /**
     * Returns an array of path segments for the provided JSON Pointer.
     * @param ptr - The JSON Pointer
     * @returns the path segments
     * @throws if the provided `ptr` argument is not a JSON Pointer
     */
    export function pathFromPtr(ptr: string): string[];

    /**
     * Returns a JSON Pointer for the provided array of path segments.
     * 
     * **Note:** If a path segment in `path` is not a `String`, it will be converted to one using `JSON.stringify`.
     * @param path - The array of path segments
     * @param hashPrefix - Whether or not create a hash-prefixed JSON Pointer
     * @returns the corresponding JSON Pointer
     * @throws if the `path` argument is not an array
     */
    export function pathToPtr(path: string[], hashPrefix?: boolean): string;

    /**
     * Finds JSON References defined within the provided array/object and resolves them.
     * @param obj - The structure to find JSON References within
     * @param options - The JsonRefs options
     * @returns a promise that resolves a
     *          {@link ResolvedRefsResults} and rejects with an `Error` when the input arguments fail validation,
     *          when `options.subDocPath` points to an invalid location or when the location argument points to an unloadable
     *          resource
     */
    export function resolveRefs(obj: any[] | object, options?: JsonRefsOptions): Promise<ResolvedRefsResults>;

    /**
     * Resolves JSON References defined within the document at the provided location.
     * 
     * This API is identical to {@link resolveRefs} except this API will retrieve a remote document and
     * then return the result of {@link resolveRefs} on the retrieved document.
     * @param location - The location to retrieve *(Can be relative or absolute, just make sure you look at the
     *        {@link JsonRefsOptions|options documentation} to see how relative references are handled.)*
     * @param options - The JsonRefs options
     * @returns a promise that resolves a
     *          {@link RetrievedResolvedRefsResults} and rejects with an `Error` when the input arguments fail
     *          validation, when `options.subDocPath` points to an invalid location or when the location argument points to an
     *          unloadable resource
     */
    export function resolveRefsAt(location: string, options?: JsonRefsOptions): Promise<RetrievedResolvedRefsResults>;

    /**
     * The options used for various JsonRefs APIs.
     */
    interface JsonRefsOptions {
        /**
         * The filter to use when gathering JSON
         * References *(If this value is a single string or an array of strings, the value(s) are expected to be the `type(s)`
         * you are interested in collecting as described in {@link getRefDetails}.  If it is a function, it is
         * expected that the function behaves like {@link RefDetailsFilter}.)*
         */
        filter?: string | string[] | Function;
        /**
         * Whether or not to include invalid JSON Reference details *(This will
         * make it so that objects that are like JSON Reference objects, as in they are an `Object` and the have a `$ref`
         * property, but fail validation will be included.  This is very useful for when you want to know if you have invalid
         * JSON Reference definitions.  This will not mean that APIs will process invalid JSON References but the reasons as to
         * why the JSON References are invalid will be included in the returned metadata.)*
         */
        includeInvalid?: boolean;
        /**
         * The options to pass to
         * {@link https://github.com/whitlockjc/path-loader/blob/master/docs/API.md#module_PathLoader.load|PathLoader~load}
         */
        loaderOptions?: object;
        /**
         * The location of the document being processed  *(This property is only
         * useful when resolving references as it will be used to locate relative references found within the document being
         * resolved. If this value is relative, {@link https://github.com/whitlockjc/path-loader|path-loader} will use
         * `window.location.href` for the browser and `process.cwd()` for Node.js.)*
         */
        location?: string;
        /**
         * The callback used to pre-process a JSON Reference like
         * object *(This is called prior to validating the JSON Reference like object and getting its details)*
         */
        refPreProcessor?: RefPreProcessor;
        /**
         * The callback used to post-process the JSON Reference
         * metadata *(This is called prior filtering the references)*
         */
        refPostProcessor?: RefPostProcessor;
        /**
         * Whether to resolve circular references
         */
        resolveCirculars?: boolean;
        /**
         * The JSON Pointer or array of path segments to the sub document
         * location to search from
         */
        subDocPath?: string | string[];
    }

    /**
     * Simple function used to filter out JSON References.
     * @param refDetails - The JSON Reference details to test
     * @param path - The path to the JSON Reference
     * @returns whether the JSON Reference should be filtered *(out)* or not
     */
    export type RefDetailsFilter = (refDetails: UnresolvedRefDetails, path: string[])=>boolean;

    /**
     * Simple function used to pre-process a JSON Reference like object.
     * @param obj - The JSON Reference like object
     * @param path - The path to the JSON Reference like object
     * @returns the processed JSON Reference like object
     */
    export type RefPreProcessor = (obj: object, path: string[])=>object;

    /**
     * Simple function used to post-process a JSON Reference details.
     * @param refDetails - The JSON Reference details to test
     * @param path - The path to the JSON Reference
     * @returns the processed JSON Reference details object
     */
    export type RefPostProcessor = (refDetails: UnresolvedRefDetails, path: string[])=>object;

    /**
     * Detailed information about resolved JSON References.
     */
    interface ResolvedRefDetails {
        /**
         * Whether or not the JSON Reference is circular *(Will not be set if the JSON
         * Reference is not circular)*
         */
        circular?: boolean;
        /**
         * The fully-qualified version of the `uri` property for
         * {@link UnresolvedRefDetails} but with the value being relative to the root document
         */
        fqURI: string;
        /**
         * Whether or not the referenced value was missing or not *(Will not be set if the
         * referenced value is not missing)*
         */
        missing?: boolean;
        /**
         * The referenced value *(Will not be set if the referenced value is missing)*
         */
        value?: any;
    }

    /**
     * The results of resolving the JSON References of an array/object.
     */
    interface ResolvedRefsResults {
        /**
         * An object whose keys are JSON Pointers *(fragment version)*
         * to where the JSON Reference is defined and whose values are {@link ResolvedRefDetails}
         */
        refs: ResolvedRefDetails;
        /**
         * The array/object with its JSON References fully resolved
         */
        resolved: object;
    }

    /**
     * An object containing the retrieved document and detailed information about its JSON References.
     */
    interface RetrievedRefsResults {
        /**
         * The retrieved document
         */
        value: object;
    }

    /**
     * An object containing the retrieved document, the document with its references resolved and  detailed information
     * about its JSON References.
     */
    interface RetrievedResolvedRefsResults {
        /**
         * An object whose keys are JSON Pointers *(fragment version)*
         * to where the JSON Reference is defined and whose values are {@link UnresolvedRefDetails}
         */
        refs: UnresolvedRefDetails;
        /**
         * The array/object with its JSON References fully resolved
         */
        resolved: object;
        /**
         * The retrieved document
         */
        value: object;
    }

    /**
     * Detailed information about unresolved JSON References.
     */
    interface UnresolvedRefDetails {
        /**
         * The JSON Reference definition
         */
        def: object;
        /**
         * The error information for invalid JSON Reference definition *(Only present when the
         * JSON Reference definition is invalid or there was a problem retrieving a remote reference during resolution)*
         */
        error?: string;
        /**
         * The URI portion of the JSON Reference
         */
        uri: string;
        /**
         * Detailed information about the URI as provided by
         * {@link https://github.com/garycourt/uri-js|URI.parse}.
         */
        uriDetails: object;
        /**
         * The JSON Reference type *(This value can be one of the following: `invalid`, `local`,
         * `relative` or `remote`.)*
         */
        type: string;
        /**
         * The warning information *(Only present when the JSON Reference definition produces a
         * warning)*
         */
        warning?: string;
    }

}

