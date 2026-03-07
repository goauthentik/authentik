import { DIFFICULTY_LEVELS, type DifficultyLevel } from "../../utils/learningCenter/utils";

export interface LearningCenterNavigationState {
    filter?: string;
    categories?: string[];
    difficulty?: DifficultyLevel | null;
}

const NAVIGATION_STATE_KEY = "authentik.learning-center.navigation-state";

function normalizeStringArray(value: unknown): string[] {
    if (!Array.isArray(value)) {
        return [];
    }

    return Array.from(
        new Set(
            value.filter((item): item is string => typeof item === "string" && item.trim() !== ""),
        ),
    );
}

function normalizeDifficulty(value: unknown): DifficultyLevel | null {
    if (typeof value !== "string") {
        return null;
    }

    const parsed = value.toLowerCase();
    return DIFFICULTY_LEVELS.includes(parsed as DifficultyLevel)
        ? (parsed as DifficultyLevel)
        : null;
}

export function writeLearningCenterNavigationState(state: LearningCenterNavigationState): void {
    if (typeof window === "undefined") {
        return;
    }

    const payload = {
        filter: typeof state.filter === "string" ? state.filter.trim() : "",
        categories: normalizeStringArray(state.categories),
        difficulty: normalizeDifficulty(state.difficulty),
    };

    window.sessionStorage.setItem(NAVIGATION_STATE_KEY, JSON.stringify(payload));
}

export function consumeLearningCenterNavigationState(): LearningCenterNavigationState {
    if (typeof window === "undefined") {
        return {};
    }

    const rawState = window.sessionStorage.getItem(NAVIGATION_STATE_KEY);
    window.sessionStorage.removeItem(NAVIGATION_STATE_KEY);

    if (!rawState) {
        return {};
    }

    try {
        const parsed = JSON.parse(rawState) as Record<string, unknown>;

        return {
            filter: typeof parsed.filter === "string" ? parsed.filter.trim() : "",
            categories: normalizeStringArray(parsed.categories),
            difficulty: normalizeDifficulty(parsed.difficulty),
        };
    } catch {
        return {};
    }
}
