/**
 * @typedef {object} AKReleasesPluginEnvironment
 * @property {string} [branch] The current branch name, if available.
 * e.g. "main" `version-${year}.${month}`, "feature-branch"
 * @property {string} currentReleaseOrigin The URL to the current release documentation.
 * @property {string} preReleaseOrigin The URL to the pre-release documentation.
 * @property {string} apiReferenceOrigin The URL to the API reference documentation.
 */

/**
 * @typedef {object} AKReleaseFrontMatter
 * @property {boolean} [draft] Whether the release is a draft.
 * @property {boolean} [unlisted] Whether the release is unlisted.
 */

/**
 * @typedef {object} AKReleaseFileMetadata
 * @property {string} name The name of the release file.
 * @property {string} path The relative path to the release file.
 */

/**
 * @typedef {AKReleaseFileMetadata & { frontMatter?: AKReleaseFrontMatter }} AKReleaseFile
 *
 * Represents a release file with additional frontmatter properties.
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
