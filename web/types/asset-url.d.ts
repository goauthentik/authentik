/**
 * @file Types for `?url` and `?worker&url` imports, which `asset-url-plugin` and Vite emit as
 *   files.
 */

declare module "*?url" {
    /**
     * URL of the emitted file, relative to the importing module.
     */
    const url: string;
    export default url;
}

declare module "*?worker&url" {
    /**
     * URL of the bundled module worker, relative to the importing module.
     */
    const url: string;
    export default url;
}
