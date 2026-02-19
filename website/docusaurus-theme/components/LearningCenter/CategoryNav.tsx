import styles from "./styles.module.css";
import { formatCategory } from "./utils";

import clsx from "clsx";
import React from "react";

/**
 * Category-based navigation for filtering resources.
 * Shows all available categories and highlights selected ones.
 */
export interface CategoryNavProps {
    availableCategories: string[];
    selectedCategories: string[];
    onToggleCategory: (category: string) => void;
}

export const CategoryNav: React.FC<CategoryNavProps> = ({
    availableCategories,
    selectedCategories,
    onToggleCategory,
}) => {
    if (availableCategories.length === 0) return null;

    return (
        <div className={styles.categoryNav}>
            <span className={styles.navLabel}>Categories:</span>
            {availableCategories.map((category) => (
                <button
                    key={category}
                    className={clsx(
                        styles.categoryButton,
                        selectedCategories.includes(category) && styles.active,
                    )}
                    onClick={() => onToggleCategory(category)}
                    aria-pressed={selectedCategories.includes(category)}
                >
                    {formatCategory(category)}
                </button>
            ))}
        </div>
    );
};

export default CategoryNav;
