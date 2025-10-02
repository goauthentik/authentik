import styles from "./styles.module.css";
import { formatTag } from "./utils";

import clsx from "clsx";
import React from "react";

/**
 * Tag-based navigation for categorized view.
 * Shows all available tags, highlights selected ones, and provides a clear action.
 */
export interface SectionNavProps {
    availableTags: string[];
    selectedTags: string[];
    onToggleTag: (tag: string) => void;
    onClear: () => void;
}

export const SectionNav: React.FC<SectionNavProps> = ({
    availableTags,
    selectedTags,
    onToggleTag,
    onClear,
}) => {
    return (
        <div className={styles.sectionNav}>
            {availableTags.map((tag) => (
                <button
                    key={tag}
                    className={clsx(
                        styles.sectionButton,
                        selectedTags.includes(tag) && styles.active,
                    )}
                    onClick={() => onToggleTag(tag)}
                >
                    {formatTag(tag)}
                </button>
            ))}
            {selectedTags.length > 0 && (
                <button
                    className={styles.clearButton}
                    onClick={onClear}
                    aria-label="Clear tag filters"
                >
                    Clear filters
                </button>
            )}
        </div>
    );
};

export default SectionNav;
