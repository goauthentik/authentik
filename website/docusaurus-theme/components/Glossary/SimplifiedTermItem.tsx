import { GlossaryTerm } from "./Glossary";
import styles from "./styles.module.css";
import { mdToHtml } from "./utils";

import React from "react";

/**
 * Compact card used in A–Z view. Renders short definition and toggle for full definition.
 */
export interface SimplifiedTermItemProps {
    term: GlossaryTerm;
    expanded: boolean;
    onToggle: () => void;
    onLinkClick: () => void;
    linkHref: string;
}

export const SimplifiedTermItem: React.FC<SimplifiedTermItemProps> = ({
    term,
    expanded,
    onToggle,
    onLinkClick,
    linkHref,
}) => {
    return (
        <div className={styles.simplifiedTermItem} id={term.id}>
            <h3 className={styles.simplifiedTermTitle}>
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
            <p
                className={styles.simplifiedDefinition}
                dangerouslySetInnerHTML={{
                    __html: term.shortHtml || mdToHtml(term.shortDefinition),
                }}
            />
            {term.fullDefinition && (
                <div>
                    <button
                        className={styles.simplifiedExpandButton}
                        onClick={onToggle}
                        aria-expanded={Boolean(expanded)}
                        aria-label={expanded ? "Collapse definition" : "Expand definition"}
                    >
                        {expanded ? "▼ Less details" : "▶ More details"}
                    </button>
                    {expanded && (
                        <div
                            className={styles.simplifiedFullDefinition}
                            dangerouslySetInnerHTML={{
                                __html: term.fullHtml || mdToHtml(term.fullDefinition),
                            }}
                        />
                    )}
                </div>
            )}
        </div>
    );
};

export default SimplifiedTermItem;
