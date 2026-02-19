import type { DifficultyLevel } from "../../theme/utils/learningCenterUtils";

export interface LearningPathDef {
    title: string;
    description: string;
    filterTag: string;
    difficulty: DifficultyLevel;
}

export const LEARNING_PATHS: LearningPathDef[] = [
    {
        title: "Getting Started with authentik",
        description: "Install, configure, and roll out your first production-ready flows.",
        filterTag: "getting-started",
        difficulty: "beginner",
    },
    {
        title: "Managing Users and Sources",
        description: "Connect identity sources and design a clean user lifecycle model.",
        filterTag: "users-sources",
        difficulty: "intermediate",
    },
    {
        title: "Security Best Practices",
        description: "Harden policies, enforce MFA, and reduce risky authentication paths.",
        filterTag: "security",
        difficulty: "advanced",
    },
    {
        title: "Providers and Protocols",
        description: "Master OAuth2/OIDC, SAML, and provider architecture decisions.",
        filterTag: "providers-protocols",
        difficulty: "advanced",
    },
    {
        title: "Fundamentals of authentik flows",
        description: "Learn how flows, stages, and policies connect across core user journeys.",
        filterTag: "fundamentals-flows",
        difficulty: "beginner",
    },
];
