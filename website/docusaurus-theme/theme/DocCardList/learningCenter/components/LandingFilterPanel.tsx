import filtersStyles from "../../../../components/LearningCenter/styling/filters.module.css";
import { formatCategory } from "../../../../components/LearningCenter/utils";
import { type DifficultyLevel, getDifficultyLabel } from "../../../utils/learningCenter/utils";

interface LandingFilterPanelProps {
    searchValue: string;
    setSearchValue: (value: string) => void;
    availableCategories: string[];
    availableDifficulties: DifficultyLevel[];
    onNavigate: (state: {
        filter?: string;
        categories?: string[];
        difficulty?: DifficultyLevel | null;
    }) => void;
}

export default function LandingFilterPanel({
    searchValue,
    setSearchValue,
    availableCategories,
    availableDifficulties,
    onNavigate,
}: LandingFilterPanelProps) {
    return (
        <div className={filtersStyles.filterModeSection}>
            <form
                className={filtersStyles.filter}
                onSubmit={(event) => {
                    event.preventDefault();
                    onNavigate({ filter: searchValue });
                }}
                role="search"
                aria-label="Search articles"
            >
                <input
                    type="search"
                    placeholder="Search articles..."
                    className={filtersStyles.filterInput}
                    value={searchValue}
                    onChange={(event) => setSearchValue(event.target.value)}
                />
                <button type="submit" className={filtersStyles.searchButton}>
                    Search
                </button>
            </form>

            {availableCategories.length > 0 ? (
                <div className={filtersStyles.quickBrowseRow}>
                    <span className={filtersStyles.navLabel}>Categories:</span>
                    {availableCategories.map((category) => (
                        <button
                            key={category}
                            type="button"
                            className={filtersStyles.categoryButton}
                            onClick={() => onNavigate({ categories: [category] })}
                        >
                            {formatCategory(category)}
                        </button>
                    ))}
                </div>
            ) : null}

            {availableDifficulties.length > 0 ? (
                <div className={filtersStyles.quickBrowseRow}>
                    <span className={filtersStyles.navLabel}>Experience Level:</span>
                    {availableDifficulties.map((difficulty) => (
                        <button
                            key={difficulty}
                            type="button"
                            className={`${filtersStyles.difficultyButton} ${filtersStyles[`difficulty-${difficulty}`]}`}
                            onClick={() => onNavigate({ difficulty })}
                        >
                            {getDifficultyLabel(difficulty)}
                        </button>
                    ))}
                </div>
            ) : null}
        </div>
    );
}
