import styles from "./styles.module.css";

import Link from "@docusaurus/Link";
import clsx from "clsx";
import React, { useMemo, useState } from "react";

export interface SectionLink {
    title: string;
    url: string;
}

export interface Section {
    title: string;
    description: string;
    links: SectionLink[];
}

export interface LearningCenterProps {
    title?: string;
    description?: string;
    sections: Section[];
    className?: string;
}

export const LearningCenter: React.FC<LearningCenterProps> = ({
    title,
    description,
    sections,
    className,
}) => {
    const [searchQuery, setSearchQuery] = useState("");

    const filteredSections = useMemo(() => {
        if (!searchQuery.trim()) return sections;

        return sections
            .map((section) => ({
                ...section,
                links: section.links.filter(
                    (link) =>
                        link.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        section.description.toLowerCase().includes(searchQuery.toLowerCase()),
                ),
            }))
            .filter(
                (section) =>
                    section.links.length > 0 ||
                    section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    section.description.toLowerCase().includes(searchQuery.toLowerCase()),
            );
    }, [sections, searchQuery]);

    return (
        <div className={clsx(styles.learningCenter, className)}>
            {(title || description) && (
                <div className={styles.header}>
                    {title && <h2 className={styles.title}>{title}</h2>}
                    {description && <p className={styles.description}>{description}</p>}
                </div>
            )}

            {sections.length > 6 && (
                <div className={styles.searchContainer}>
                    <div className={styles.searchInputWrapper}>
                        <svg
                            className={styles.searchIcon}
                            width="16"
                            height="16"
                            viewBox="0 0 16 16"
                            fill="none"
                        >
                            <path
                                d="M7.333 12.667A5.333 5.333 0 1 0 7.333 2a5.333 5.333 0 0 0 0 10.667ZM14 14l-2.9-2.9"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </svg>
                        <input
                            type="text"
                            placeholder="Search learning resources..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className={styles.searchInput}
                            aria-label="Search learning resources"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery("")}
                                className={styles.clearButton}
                                aria-label="Clear search"
                            >
                                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                    <path
                                        d="M10.5 3.5L3.5 10.5M3.5 3.5l7 7"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>
            )}

            {searchQuery && filteredSections.length === 0 && (
                <div className={styles.noResults}>
                    <svg
                        className={styles.noResultsIcon}
                        width="48"
                        height="48"
                        viewBox="0 0 24 24"
                        fill="none"
                    >
                        <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
                        <path d="m21 21-4.35-4.35" stroke="currentColor" strokeWidth="2" />
                        <path
                            d="M11 7.5c-2 0-3.5 1.5-3.5 3.5"
                            stroke="currentColor"
                            strokeWidth="2"
                        />
                    </svg>
                    <h3>No results found</h3>
                    <p>Try adjusting your search terms or browse all sections below.</p>
                    <button onClick={() => setSearchQuery("")} className={styles.clearSearchButton}>
                        Clear search
                    </button>
                </div>
            )}

            <div className={styles.sectionGrid}>
                {filteredSections.map((section, idx) => (
                    <div key={idx} className={styles.sectionCard}>
                        <div className={styles.sectionContent}>
                            <h3 className={styles.sectionTitle}>{section.title}</h3>
                            <p className={styles.sectionDescription}>{section.description}</p>
                        </div>
                        {section.links && section.links.length > 0 && (
                            <div className={styles.sectionLinks}>
                                {section.links.map((link, linkIdx) => (
                                    <Link
                                        key={linkIdx}
                                        to={link.url}
                                        className={styles.sectionLink}
                                        aria-label={`Go to ${link.title}`}
                                    >
                                        <svg
                                            className={styles.linkIcon}
                                            width="14"
                                            height="14"
                                            viewBox="0 0 14 14"
                                            fill="none"
                                        >
                                            <path
                                                d="M5.25 10.5L8.75 7L5.25 3.5"
                                                stroke="currentColor"
                                                strokeWidth="2"
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                            />
                                        </svg>
                                        <span>{link.title}</span>
                                    </Link>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default LearningCenter;
