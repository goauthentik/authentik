import styles from "./styles.module.css";

import React from "react";

/** Controlled filter input with a clear button. */
export interface FilterInputProps {
    value: string;
    onChange: (value: string) => void;
    onClear: () => void;
}

export const FilterInput: React.FC<FilterInputProps> = ({ value, onChange, onClear }) => {
    return (
        <div className={styles.filter}>
            <input
                type="text"
                placeholder="Filter terms..."
                className={styles.filterInput}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                aria-label="Filter glossary terms"
            />
            {value && (
                <button className={styles.clearButton} onClick={onClear} aria-label="Clear filter">
                    Clear
                </button>
            )}
        </div>
    );
};

export default FilterInput;
