import type { Locator } from "@playwright/test";

export type LocatorContext = Pick<
    Locator,
    | "locator"
    | "getByRole"
    | "getByTestId"
    | "getByText"
    | "getByLabel"
    | "getByAltText"
    | "getByTitle"
    | "getByPlaceholder"
>;
