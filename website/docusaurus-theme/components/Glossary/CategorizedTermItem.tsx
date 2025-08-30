import { GlossaryTerm } from "./Glossary";
import styles from "./styles.module.css";
import { mdToHtml } from "./utils";

import React from "react";

/**
 * Full-sized item used in categorized view. Shows short definition and expandable full definition.
 */
export interface CategorizedTermItemProps {
    term: GlossaryTerm;
    expanded: boolean;
    onToggle: () => void;
    onLinkClick: () => void;
    linkHref: string;
}

export const CategorizedTermItem: React.FC<CategorizedTermItemProps> = ({
    term,
    expanded,
    onToggle,
    onLinkClick,
    linkHref,
}) => {
    return (
        <div className={styles.termItem} id={term.id}>
            <div className={styles.termHeader}>
                <h3 className={styles.termTitle}>
                    {term.term}
                    <a
                        href={linkHref}
                        onClick={(e) => {
                            e.preventDefault();
                            onLinkClick();
                        }}
                        className={styles.anchorLink}
                        aria-label={`Copy link to ${term.term}`}
                    >
                        ¶
                    </a>
                </h3>
                {term.fullDefinition && (
                    <button
                        className={styles.expandButton}
                        onClick={onToggle}
                        aria-expanded={Boolean(expanded)}
                        aria-label={expanded ? "Collapse definition" : "Expand definition"}
                    >
                        {expanded ? "▼ Less" : "▶ More"}
                    </button>
                )}
            </div>
            <p
                className={styles.shortDefinition}
                dangerouslySetInnerHTML={{
                    __html: term.shortHtml || mdToHtml(term.shortDefinition),
                }}
            />
            {term.fullDefinition && expanded && (
                <div className={styles.fullDefinition}>
                    <div
                        dangerouslySetInnerHTML={{
                            __html: term.fullHtml || mdToHtml(term.fullDefinition),
                        }}
                    />
                </div>
            )}
        </div>
    );
};

export default CategorizedTermItem;
