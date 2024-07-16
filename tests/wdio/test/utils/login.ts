import LoginPage from "../pageobjects/login.page.js";
import { GOOD_PASSWORD, GOOD_USERNAME } from "./constants.js";

export const login = async () => {
    await LoginPage.open();
    await LoginPage.login(GOOD_USERNAME, GOOD_PASSWORD);
};
