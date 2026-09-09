import useBaseUrl from "@docusaurus/useBaseUrl";
import React, { type ReactNode } from "react";

// Use this for static file download links, including bundled blueprints.
// Docusaurus rewrites Markdown static-asset links into hashed asset URLs, which
// caused blueprint downloads to lose their useful filenames:
// https://github.com/goauthentik/authentik/issues/20089

interface DownloadLinkProps {
    children: ReactNode;
    filename?: string;
    to: string;
}

function getFilename(path: string): string {
    return path.split("/").filter(Boolean).at(-1) ?? "";
}

export default function DownloadLink({ children, filename, to }: DownloadLinkProps): ReactNode {
    const href = useBaseUrl(to);
    const download = filename ?? getFilename(to);

    return (
        <a href={href} download={download}>
            {children}
        </a>
    );
}
