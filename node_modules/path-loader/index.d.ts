/**
 * Utility that provides a single API for loading the content of a path/URL.
 */
declare module 'path-loader' {
    /**
     * Loads a document at the provided location and returns a JavaScript object representation.
     * @param location - The location to the document
     * @param options - The loader options
     * @returns Always returns a promise even if there is a callback provided
     */
    export function load(location: string, options?: module:path-loader.LoadOptions): Promise<any>;

    /**
     * Options used when loading a path.
     */
    interface LoadOptions {
        /**
         * The encoding to use when loading the file *(File loader only)*
         */
        encoding?: string;
        /**
         * The HTTP method to use for the request *(HTTP loader only)*
         */
        method?: string;
        /**
         * The callback used to prepare the request *(HTTP loader only)*
         */
        prepareRequest?: module:path-loader.PrepareRequestCallback;
        /**
         * The callback used to process the response
         */
        processContent?: module:path-loader.ProcessResponseCallback;
    }

    /**
     * Callback used to provide access to altering a remote request prior to the request being made.
     * @param req - The Superagent request object
     * @param location - The location being retrieved
     * @param callback - First callback
     */
    export type PrepareRequestCallback = (req: object, location: string, callback: Function)=>void;

    /**
     * Callback used to provide access to processing the raw response of the request being made. *(HTTP loader only)*
     * @param res - The Superagent response object *(For non-HTTP loaders, this object will be like the Superagent
     *        object in that it will have a `text` property whose value is the raw string value being processed.  This was done
     *        for consistency.  There will also be a `location` property containing the location of the path being loaded.)*
     * @param callback - Error-first callback
     * @returns the result of processing the responses
     */
    export type ProcessResponseCallback = (res: object, callback: Function)=>any;

}

