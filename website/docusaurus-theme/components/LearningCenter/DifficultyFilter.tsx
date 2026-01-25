import { type DifficultyLevel, getDifficultyLabel } from "../../theme/utils/learningCenterUtils";
import styles from "./styles.module.css";

import clsx from "clsx";
import React from "react";

/**
 * Difficulty level filter for resources.
 */
export interface DifficultyFilterProps {
    availableDifficulties: DifficultyLevel[];
    selectedDifficulty: DifficultyLevel | null;
    onSelectDifficulty: (difficulty: DifficultyLevel | null) => void;
}

export const DifficultyFilter: React.FC<DifficultyFilterProps> = ({
    availableDifficulties,
    selectedDifficulty,
    onSelectDifficulty,
}) => {
    if (availableDifficulties.length === 0) return null;

    return (
        <div className={styles.difficultyFilter}>
            <span className={styles.navLabel}>Difficulty:</span>
            <button
                className={clsx(
                    styles.difficultyButton,
                    selectedDifficulty === null && styles.active,
                )}
                onClick={() => onSelectDifficulty(null)}
                aria-pressed={selectedDifficulty === null}
            >
                All
            </button>
            {availableDifficulties.map((difficulty) => (
                <button
                    key={difficulty}
                    className={clsx(
                        styles.difficultyButton,
                        styles[`difficulty-${difficulty}`],
                        selectedDifficulty === difficulty && styles.active,
                    )}
                    onClick={() => onSelectDifficulty(difficulty)}
                    aria-pressed={selectedDifficulty === difficulty}
                >
                    {getDifficultyLabel(difficulty)}
                </button>
            ))}
        </div>
    );
};

export default DifficultyFilter;
