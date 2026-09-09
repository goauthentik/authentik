import styles from "./styles.module.css";
import { formatTag } from "./utils";

import clsx from "clsx";
import React from "react";

/**
 * Tag-based navigation for categorized view.
 * Shows all available tags and highlights selected ones.
 */
export interface SectionNavProps {
    availableTags: string[];
    selectedTags: string[];
    onToggleTag: (tag: string) => void;
}

export const SectionNav: React.FC<SectionNavProps> = ({
    availableTags,
    selectedTags,
    onToggleTag,
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
        </div>
    );
};

export default SectionNav;
