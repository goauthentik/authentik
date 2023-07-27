import React from "react";
import sidebar from "../../../sidebars";
import "./style.css";
import useBaseUrl from "@docusaurus/useBaseUrl";

interface ItemLink {
    label: string;
    link: string;
}

export function getReleases(): ItemLink[] {
    const docs = sidebar.docs;
    const releaseCategory = docs.filter(
        (doc) => doc.link?.slug === "releases",
    )[0];
    // @ts-ignore
    const releaseItems = releaseCategory.items!.filter(
        (release) => typeof release === "string",
    );
    const releaseVersion: ItemLink[] = releaseItems.map((relUrl: string) => {
        const [_, year, version] = relUrl.split("/");
        return {
            label: `authentik ${version} released!`,
            link: relUrl,
        };
    });
    return releaseVersion;
}

export function NewsBar() {
    return (
        <div className="news-bar-container">
            <span>News</span>
            <div className="items">
                {getReleases().map((version) => {
                    return (
                        <a key={version.link} href={useBaseUrl(version.link)}>
                            {version.label}
                        </a>
                    );
                })}
            </div>
        </div>
    );
}
