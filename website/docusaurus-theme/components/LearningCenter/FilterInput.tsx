import styles from "./styles.module.css";

import React from "react";

/** Controlled filter input with a clear button. */
export interface FilterInputProps {
    value: string;
    onChange: (value: string) => void;
    onClear: () => void;
    placeholder?: string;
}

export const FilterInput: React.FC<FilterInputProps> = ({
    value,
    onChange,
    onClear,
    placeholder = "Search articles...",
}) => {
    return (
        <div className={styles.filter}>
            <input
                type="text"
                placeholder={placeholder}
                className={styles.filterInput}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                aria-label="Filter learning resources"
            />
            {value ? (
                <button className={styles.clearButton} onClick={onClear} aria-label="Clear filter">
                    Clear
                </button>
            ) : null}
        </div>
    );
};

export default FilterInput;
