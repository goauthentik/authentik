import { expect } from "@wdio/globals";

import LoginPage from "../pageobjects/login.page.js";
import UserLibraryPage from "../pageobjects/user-library.page.js";
import { GOOD_PASSWORD, GOOD_USERNAME } from "./constants.js";

export const login = async () => {
    await LoginPage.open();
    await LoginPage.login(GOOD_USERNAME, GOOD_PASSWORD);
    await expect(await UserLibraryPage.pageHeader()).toHaveText("My applications");
};
