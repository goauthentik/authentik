/**
 * @file Web component globals applied to the Window object.
 *
 * @see https://www.npmjs.com/package/@webcomponents/webcomponentsjs
 */

export {};

declare global {
    type Booleanish = "true" | "false";

    type WebComponentFlags = Record<string, Booleanish | boolean | Record<string, boolean>>;

    interface WebComponents {
        /**
         * Flags that can be set on the `WebComponents` global to control the behavior of web components in the application.
         * Typically, this is limited to the `webcomponents-loader`.
         */
        flags?: WebComponentFlags;
    }

    interface ShadyDOM {
        /**
         * Forces the use of the Shady DOM polyfill, even in browsers that support native Shadow DOM.
         * This can be useful for testing or to work around specific issues with native Shadow DOM in certain browsers.
         */
        force?: boolean | Booleanish;
        /**
         * Prevents the patching of native Shadow DOM APIs when the Shady DOM polyfill is in use.
         * This can be useful for debugging or to avoid conflicts with other libraries that also patch these APIs.
         */
        noPatch?: boolean | Booleanish;
    }

    interface CustomElementRegistry {
        /**
         * An indication of whether the polyfill for web components is in use.
         */
        readonly forcePolyfill?: Booleanish | boolean;
    }

    interface Window {
        /**
         * An object representing the state of web component support and configuration in the application.
         */
        WebComponents?: Readonly<WebComponents>;
        /**
         * An object representing the configuration for the Shady DOM polyfill,
         * which provides support for Shadow DOM in browsers that do not natively support it.
         */
        ShadyDOM?: Readonly<ShadyDOM>;
        /**
         * A root path for loading web component polyfills. This is only applicable
         *
         * @remarks
         * If you're using the loader on a page that enforces the `trusted-types`
         * Content Security Policy, you'll need to allow the `webcomponents-loader`
         * policy name so that the loader can dynamically create and insert a `<script>`
         * for the polyfill bundle it selects based on feature detection. I
         * f you set `WebComponents.root` (which is rare), it should be set to a {@linkcode TrustedScriptURL}
         * for Trusted Types compatibility.
         */
        root?: string | TrustedScriptURL;
    }
}
