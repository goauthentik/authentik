/**
 * Create a URL to GH.
 *
 * @satisfies {BuildUrl}
 * @param {Readonly<BuildUrlValues>} values
 *   Info on the link to build.
 * @returns {string}
 *   URL to use.
 */
export function defaultBuildUrl(values: Readonly<BuildUrlValues>): string;
/**
 * Link references to users, commits, and issues, in the same way that GitHub
 * does in comments, issues, PRs, and releases.
 *
 * @param {Readonly<Options> | null | undefined} [options]
 *   Configuration (optional).
 * @returns
 *   Transform.
 */
export default function remarkGithub(options?: Readonly<Options> | null | undefined): (tree: Root, file: VFile) => undefined;
export type PhrasingContent = import('mdast').PhrasingContent;
export type Root = import('mdast').Root;
export type ReplaceFunction = import('mdast-util-find-and-replace').ReplaceFunction;
export type RegExpMatchObject = import('mdast-util-find-and-replace').RegExpMatchObject;
export type VFile = import('vfile').VFile;
/**
 * Create a URL.
 */
export type BuildUrl = (values: Readonly<BuildUrlValues>) => string | false;
/**
 * Info for commit hash.
 */
export type BuildUrlCommitValues = {
    /**
     *   Commit hash value.
     */
    hash: string;
    /**
     *   Project name.
     */
    project: string;
    /**
     *   Kind.
     */
    type: 'commit';
    /**
     *   Owner of repo.
     */
    user: string;
};
/**
 * Info for commit hash ranges.
 */
export type BuildUrlCompareValues = {
    /**
     *   SHA of the range start.
     */
    base: string;
    /**
     *   SHA of the range end.
     */
    compare: string;
    /**
     *   Project name.
     */
    project: string;
    /**
     *   Kind.
     */
    type: 'compare';
    /**
     *   Owner of repo.
     */
    user: string;
};
/**
 * Info for issues.
 */
export type BuildUrlIssueValues = {
    /**
     *   Issue number.
     */
    no: string;
    /**
     *   Project name.
     */
    project: string;
    /**
     *   Kind.
     */
    type: 'issue';
    /**
     *   Owner of repo.
     */
    user: string;
};
/**
 * Info for mentions.
 */
export type BuildUrlMentionValues = {
    /**
     *   Kind.
     */
    type: 'mention';
    /**
     *   User name.
     */
    user: string;
};
/**
 * Info.
 */
export type BuildUrlValues = BuildUrlCommitValues | BuildUrlCompareValues | BuildUrlIssueValues | BuildUrlMentionValues;
/**
 * Configuration.
 */
export type Options = {
    /**
     * Change how things are linked (optional).
     */
    buildUrl?: BuildUrl | null | undefined;
    /**
     * Wrap mentions in `strong` (default: `true`);
     * this makes them render more like how GitHub styles them, but GH itself
     * uses CSS instead of `strong`.
     */
    mentionStrong?: boolean | null | undefined;
    /**
     * Repository to link against (default: `repository` from `packag.json` in CWD in Node);
     * should point to a GitHub repository (such as `'user/project'`)
     */
    repository?: string | null | undefined;
};
/**
 * Owner and project of repo.
 */
export type RepositoryInfo = {
    /**
     *   Project name.
     */
    project: string;
    /**
     *   User/organization name.
     */
    user: string;
};
/**
 * Info.
 */
export type UrlInfo = {
    /**
     *   Whether the link is to a comment.
     */
    comment: boolean;
    /**
     *   Page type.
     */
    page: string;
    /**
     *   Project name.
     */
    project: string;
    /**
     *   Reference.
     */
    reference: string;
    /**
     *   User/organization name.
     */
    user: string;
};
