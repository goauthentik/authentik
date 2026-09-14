declare module "rapidoc" {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    type Booleanish = "true" | "false";

    /**
     * Web Component based Swagger & OpenAPI Spec Viewer
     *
     * @element rapi-doc
     *
     * @attr {string} spec-url - URL of the OpenAPI spec to view.
     * @attr {Booleanish} update-route - Setting true will update the browser URL when a new section is visited. Default: true.
     * @attr {string} route-prefix - Custom prefix for generated routes to support third-party routing. Default: "#".
     * @attr {Booleanish} sort-tags - List tags in alphabetical order instead of spec order. Default: false.
     * @attr {Booleanish} sort-schemas - List schemas in alphabetical order (only in focused render-style with show-components). Default: false.
     * @attr {"path" | "method" | "summary" | "none"} sort-endpoints-by - Sort endpoints within each tag. Default: "path".
     * @attr {string} heading-text - Heading text displayed on the top-left corner.
     * @attr {string} goto-path - Initial location after spec loads, in format {method}-{path} (e.g., "get-/user/login").
     * @attr {Booleanish} fill-request-fields-with-example - Fill request fields with example values from spec. Default: true.
     * @attr {Booleanish} persist-auth - Persist authentication to localStorage. Default: false.
     * @attr {"light" | "dark"} theme - Base theme for calculating UI colors. Default: "dark".
     * @attr {string} bg-color - Hex color code for main background (dark: #333, light: #fff).
     * @attr {string} text-color - Hex color code for text (dark: #bbb, light: #444).
     * @attr {string} header-color - Hex color code for header background. Default: "#444444".
     * @attr {string} primary-color - Hex color code for buttons, tabs, and controls. Default: "#FF791A".
     * @attr {Booleanish} load-fonts - Load fonts from CDN. Default: true.
     * @attr {string} regular-font - Font name(s) for regular text. Default: '"Open Sans", Avenir, "Segoe UI", Arial, sans-serif'.
     * @attr {string} mono-font - Font name(s) for mono-spaced text. Default: "Monaco, 'Andale Mono', 'Roboto Mono', 'Consolas' monospace".
     * @attr {"default" | "large" | "largest"} font-size - Relative font size for the entire document. Default: "default".
     * @attr {string} css-file - Name of external CSS file to inject custom styles.
     * @attr {string} css-classes - Space-separated CSS class names to apply to RapiDoc element.
     * @attr {"false" | "as-plain-text" | "as-colored-text" | "as-colored-block"} show-method-in-nav-bar - Show API method names in navigation bar. Default: "false".
     * @attr {Booleanish} use-path-in-nav-bar - Show API paths instead of summary/description in nav bar. Default: false.
     * @attr {string} nav-bg-color - Navigation bar background color.
     * @attr {string} nav-text-color - Navigation bar text color.
     * @attr {string} nav-hover-bg-color - Navigation item background color on hover.
     * @attr {string} nav-hover-text-color - Navigation item text color on hover.
     * @attr {string} nav-accent-color - Accent color for navigation bar (e.g., active item background).
     * @attr {string} nav-accent-text-color - Text color for selected navigation items.
     * @attr {"left-bar" | "colored-block"} nav-active-item-marker - Navigation active item indicator style. Default: "left-bar".
     * @attr {"default" | "compact" | "relaxed"} nav-item-spacing - Navigation item spacing. Default: "default".
     * @attr {"expand-collapse" | "show-description"} on-nav-tag-click - Behavior when clicking a tag in focused mode. Default: "expand-collapse".
     * @attr {"row" | "column"} layout - Placement of request/response sections (side-by-side or stacked). Default: "row".
     * @attr {"read" | "view" | "focused"} render-style - Display mode for API docs. Default: "read".
     * @attr {string} response-area-height - Height of response textarea (e.g., "400px", "50%", "60vh"). Default: "300px".
     * @attr {Booleanish} show-info - Show/hide the document info section (title, description, version, etc.). Default: true.
     * @attr {Booleanish} info-description-headings-in-navbar - Include h1/h2 headers from info description in navigation (read mode). Default: false.
     * @attr {string} match-paths - Filter to show only APIs matching this path (substring or regex based on match-type).
     * @attr {"includes" | "regex"} match-type - How match-paths filtering is applied. Default: "includes".
     * @attr {string} remove-endpoints-with-badge-label-as - Comma-separated badge labels to remove from spec.
     * @attr {Booleanish} show-components - Show components section (schemas, responses, etc.) in focused render-style. Default: false.
     * @attr {Booleanish} show-header - Show/hide the header. Default: true.
     * @attr {Booleanish} allow-authentication - Show/hide authentication section. Default: true.
     * @attr {Booleanish} allow-spec-url-load - Allow loading spec URL from UI. Default: true.
     * @attr {Booleanish} allow-spec-file-load - Allow loading spec file from local drive (devices > 768px). Default: true.
     * @attr {Booleanish} allow-spec-file-download - Show buttons to download spec or open in new tab. Default: false.
     * @attr {Booleanish} allow-search - Enable quick filtering of APIs. Default: true.
     * @attr {Booleanish} allow-advanced-search - Enable searching through paths, descriptions, parameters, and responses. Default: true.
     * @attr {Booleanish} allow-try - Enable the TRY feature for making REST calls. Default: true.
     * @attr {Booleanish} show-curl-before-try - Display cURL snippet between request and response without clicking TRY. Default: false.
     * @attr {Booleanish} allow-server-selection - Allow user to see/select API server. Default: true.
     * @attr {Booleanish} allow-schema-description-expand-toggle - Allow expanding/collapsing field descriptions in schema. Default: true.
     * @attr {"tree" | "table"} schema-style - Display style for object-schemas. Default: "tree".
     * @attr {number} schema-expand-level - Number of levels to expand in schema. Default: 999.
     * @attr {Booleanish} schema-description-expanded - Fully expand constraint/description info. Default: false.
     * @attr {"default" | "never"} schema-hide-read-only - Hide read-only schema attributes in requests. Default: "default".
     * @attr {"default" | "never"} schema-hide-write-only - Hide write-only schema attributes in responses. Default: "default".
     * @attr {"schema" | "example" | "model"} default-schema-tab - Default active tab for schema display. Default: "model".
     * @attr {string} server-url - Custom API server URL not listed in spec.
     * @attr {string} default-api-server - Default API server from spec for API calls.
     * @attr {string} api-key-name - Name of the API key for TRY requests.
     * @attr {"header" | "query"} api-key-location - How to send the API key.
     * @attr {string} api-key-value - Value of the API key (can be overwritten from UI).
     * @attr {"omit" | "same-origin" | "include"} fetch-credentials - Credentials mode for cross-domain calls.
     */
    class RapiDoc extends HTMLElement {
        /**
         * Programmatically load a spec.
         * @param spec - URL string or JSON object representing a valid OpenAPI spec.
         */
        loadSpec(spec: string | object): void;

        /**
         * Programmatically scroll to a section identified by method and path.
         * @param path - Path in format {method}-{path} (e.g., "get-/user/login").
         */
        scrollToPath(path: string): void;

        /**
         * Programmatically provide HTTP Basic username and password.
         * @param securitySchemeId - A valid securityScheme ID defined in the spec.
         * @param username - The username.
         * @param password - The password.
         */
        setHttpUserNameAndPassword(
            securitySchemeId: string,
            username: string,
            password: string,
        ): void;

        /**
         * Programmatically provide an API key.
         * @param securitySchemeId - A valid securityScheme ID defined in the spec.
         * @param token - The API key token.
         */
        setApiKey(securitySchemeId: string, token: string): void;

        /**
         * Programmatically set the API server.
         * @param apiServerUrl - A valid server URL defined in the spec.
         */
        setApiServer(apiServerUrl: string): void;
    }

    export default RapiDoc;
}
