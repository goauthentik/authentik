import styles from "./styles.module.css";

import clsx from "clsx";
import React from "react";

export type ViewMode = "categorized" | "alphabetical" | "grid";

/**
 * Toggle between different view modes in the learning center.
 */
export interface ViewToggleProps {
    viewMode: ViewMode;
    onChange: (mode: ViewMode) => void;
}

export const ViewToggle: React.FC<ViewToggleProps> = ({ viewMode, onChange }) => {
    return (
        <div className={styles.viewToggleContainer}>
            <p className={styles.viewTogglePrompt}>View:</p>
            <button
                className={clsx(
                    styles.viewToggle,
                    viewMode === "categorized" && styles.viewToggleActive,
                )}
                onClick={() => onChange("categorized")}
                aria-pressed={viewMode === "categorized"}
            >
                Categories
            </button>
            <button
                className={clsx(
                    styles.viewToggle,
                    viewMode === "alphabetical" && styles.viewToggleActive,
                )}
                onClick={() => onChange("alphabetical")}
                aria-pressed={viewMode === "alphabetical"}
            >
                A-Z
            </button>
            <button
                className={clsx(styles.viewToggle, viewMode === "grid" && styles.viewToggleActive)}
                onClick={() => onChange("grid")}
                aria-pressed={viewMode === "grid"}
            >
                Grid
            </button>
        </div>
    );
};

export default ViewToggle;
