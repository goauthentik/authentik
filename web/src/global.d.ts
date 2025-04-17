/**
 * @file Global type declarations.
 */

// TODO: Come back to this. Maybe fix with ESBuild plugin?
// declare module "*.css" {
//     /**
//      * The style content of a CSS file.
//      */
//     const content: string;

//     export default content;
// }

/**
 * The style content of a CSS file.
 */
declare module "*.css";

declare module "*.md" {
    /**
     * The serialized JSON content of an MD file.
     */
    const serializedJSON: string;
    export default serializedJSON;
}

declare module "*.mdx" {
    /**
     * The serialized JSON content of an MDX file.
     */
    const serializedJSON: string;
    export default serializedJSON;
}

declare namespace Intl {
    class ListFormat {
        constructor(locale: string, args: { [key: string]: string });
        public format: (items: string[]) => string;
    }
}
