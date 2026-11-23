/**
 * @typedef {object} AKReleasesPluginEnvironment
 * @property {string} [branch] The current branch name, if available.
 *   e.g. "main" `version-${year}.${month}`, "feature-branch"
 * @property {string} currentReleaseOrigin The URL to the current release documentation.
 * @property {string} preReleaseOrigin The URL to the pre-release documentation.
 * @property {string} apiReferenceOrigin The URL to the API reference documentation.
 */

/**
 * @typedef {object} AKReleaseFrontMatter
 * @property {boolean} [beta] Whether the release is a beta.
 * @property {boolean} [draft] Whether the release is a draft.
 * @property {boolean} [unlisted] Whether the release is unlisted.
 */

/**
 * @typedef {object} AKReleaseFileMetadata
 * @property {string} name The release version, e.g. "2026.11".
 * @property {string} path The release doc ID: the file path without its extension.
 * @property {string} [filePath] The release file path, relative to the docs directory.
 */

/**
 * @typedef {AKReleaseFileMetadata & { frontMatter?: AKReleaseFrontMatter }} AKReleaseFile
 *
 *   Represents a release file with additional frontmatter properties.
 */

/**
 * @typedef {object} AKReleasesPluginOptions
 * @property {string} docsDirectory The path to the documentation directory.
 * @property {AKReleasesPluginEnvironment} [environment] Optional environment variables overrides.
 */

/**
 * @typedef {object} AKReleasesPluginData
 * @property {string} publicPath URL to the plugin's public directory.
 * @property {AKReleaseFile[]} releases Available versions of the documentation.
 * @property {AKReleasesPluginEnvironment} env Environment variables
 */

export {};
