import styles from "./styles.module.css";

import clsx from "clsx";
import React from "react";

/**
 * Toggle between categorized and A–Z views in the glossary.
 */
export interface ViewToggleProps {
    isSimplifiedView: boolean;
    onChange: (simplified: boolean) => void;
}

export const ViewToggle: React.FC<ViewToggleProps> = ({ isSimplifiedView, onChange }) => {
    return (
        <div className={styles.viewToggleContainer}>
            <p className={styles.viewTogglePrompt}>Views:</p>
            <button
                className={clsx(styles.viewToggle, isSimplifiedView && styles.viewToggleActive)}
                onClick={() => onChange(true)}
                aria-pressed={isSimplifiedView}
            >
                A-Z
            </button>
            <button
                className={clsx(styles.viewToggle, !isSimplifiedView && styles.viewToggleActive)}
                onClick={() => onChange(false)}
                aria-pressed={!isSimplifiedView}
            >
                Tags
            </button>
        </div>
    );
};

export default ViewToggle;
