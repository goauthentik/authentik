import useIsBrowser from "@docusaurus/useIsBrowser";
import React from "react";
import { coerce } from "semver";

export interface AuthentikVersionProps {
    semver: string;
}

/**
 * Badge indicating semantic versioning of authentik required for a feature or integration.
 */
export const VersionBadge: React.FC<AuthentikVersionProps> = ({ semver }) => {
    const parsed = coerce(semver);

    if (!parsed) {
        throw new Error(`Invalid semver version: ${semver}`);
    }

    const yearCutoff = new Date().getFullYear() - 2;
    const isBrowser = useIsBrowser();
    const onError = (err: Error) => {
        if (isBrowser) {
            console.warn(err);
        } else {
            throw err;
        }
    };


    if (parsed.major <= yearCutoff) {
        onError(new Error(`Semver version <= ${yearCutoff} is not supported: ${semver}`));
    }

    return (
        <span
            title={`Available in authentik ${parsed.format()} and later`}
            aria-description="Version badge"
            role="img"
            className="badge badge--version"
        >
            authentik:&nbsp;{parsed.format()}+
        </span>
    );
};

export default VersionBadge;
