"""Test 2-step enroll flow"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from e2e.utils import USER, SeleniumTestCase


class TestEnroll2Step(SeleniumTestCase):
    """Test 2-step enroll flow"""

    # pylint: disable=too-many-statements
    def setup_test_enroll_2_step(self):
        """Setup all required objects"""
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.LINK_TEXT, "Administrate").click()
        self.driver.find_element(By.LINK_TEXT, "Prompts").click()

        # Create Password Prompt
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_field_key").send_keys("password")
        self.driver.find_element(By.ID, "id_label").send_keys("Password")
        dropdown = self.driver.find_element(By.ID, "id_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Password']").click()
        self.driver.find_element(By.ID, "id_placeholder").send_keys("Password")
        self.driver.find_element(By.ID, "id_order").send_keys("1")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Password Repeat Prompt
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_field_key").send_keys("password_repeat")
        self.driver.find_element(By.ID, "id_label").send_keys("Password (repeat)")
        dropdown = self.driver.find_element(By.ID, "id_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Password']").click()
        self.driver.find_element(By.ID, "id_placeholder").send_keys("Password (repeat)")
        self.driver.find_element(By.ID, "id_order").send_keys("2")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Name Prompt
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_field_key").send_keys("name")
        self.driver.find_element(By.ID, "id_label").send_keys("Name")
        dropdown = self.driver.find_element(By.ID, "id_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Text']").click()
        self.driver.find_element(By.ID, "id_placeholder").send_keys("Name")
        self.driver.find_element(By.ID, "id_order").send_keys("0")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Email Prompt
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_field_key").send_keys("email")
        self.driver.find_element(By.ID, "id_label").send_keys("Email")
        dropdown = self.driver.find_element(By.ID, "id_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Email']").click()
        self.driver.find_element(By.ID, "id_placeholder").send_keys("Email")
        self.driver.find_element(By.ID, "id_order").send_keys("1")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(By.LINK_TEXT, "Stages").click()

        # Create first enroll prompt stage
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(9) > .pf-c-dropdown__menu-item > small"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys(
            "enroll-prompt-stage-first"
        )
        dropdown = self.driver.find_element(By.ID, "id_fields")
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'username' type=text\"]"
        ).click()
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'password' type=password\"]"
        ).click()
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'password_repeat' type=password\"]"
        ).click()
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create second enroll prompt stage
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(9) > .pf-c-dropdown__menu-item"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys(
            "enroll-prompt-stage-second"
        )
        dropdown = self.driver.find_element(By.ID, "id_fields")
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'name' type=text\"]"
        ).click()
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'email' type=email\"]"
        ).click()
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create user write stage
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(13) > .pf-c-dropdown__menu-item"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys("enroll-user-write")
        self.driver.find_element(By.ID, "id_name").send_keys(Keys.ENTER)
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()

        # Create user login stage
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(11) > .pf-c-dropdown__menu-item"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys("enroll-user-login")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(
            By.CSS_SELECTOR,
            ".pf-c-nav__item:nth-child(7) .pf-c-nav__item:nth-child(1) > .pf-c-nav__link",
        ).click()

        # Create password policy
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(2) > .pf-c-dropdown__menu-item > small"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys(
            "policy-enrollment-password-equals"
        )
        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, ".CodeMirror-scroll"))
        )
        self.driver.find_element(By.CSS_SELECTOR, ".CodeMirror-scroll").click()
        self.driver.find_element(By.CSS_SELECTOR, ".CodeMirror textarea").send_keys(
            "return request.context['password'] == request.context['password_repeat']"
        )
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create password policy binding
        self.driver.find_element(
            By.CSS_SELECTOR,
            ".pf-c-nav__item:nth-child(7) .pf-c-nav__item:nth-child(2) > .pf-c-nav__link",
        ).click()
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        dropdown = self.driver.find_element(By.ID, "id_policy")
        dropdown.find_element(
            By.XPATH, '//option[. = "Policy policy-enrollment-password-equals"]'
        ).click()
        self.driver.find_element(By.ID, "id_target").click()
        dropdown = self.driver.find_element(By.ID, "id_target")
        dropdown.find_element(
            By.XPATH, '//option[. = "Prompt Stage enroll-prompt-stage-first"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").send_keys("0")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Flow
        self.driver.find_element(
            By.CSS_SELECTOR,
            ".pf-c-nav__item:nth-child(6) .pf-c-nav__item:nth-child(1) > .pf-c-nav__link",
        ).click()
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_name").send_keys("Welcome")
        self.driver.find_element(By.ID, "id_slug").clear()
        self.driver.find_element(By.ID, "id_slug").send_keys("default-enrollment-flow")
        dropdown = self.driver.find_element(By.ID, "id_designation")
        dropdown.find_element(By.XPATH, '//option[. = "Enrollment"]').click()
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(By.LINK_TEXT, "Stages").click()

        # Edit identification stage
        self.driver.find_element(
            By.CSS_SELECTOR, "tr:nth-child(11) .pf-m-secondary"
        ).click()
        self.driver.find_element(
            By.CSS_SELECTOR,
            ".pf-c-form__group:nth-child(5) .pf-c-form__horizontal-group",
        ).click()
        self.driver.find_element(By.ID, "id_enrollment_flow").click()
        dropdown = self.driver.find_element(By.ID, "id_enrollment_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        self.driver.find_element(By.ID, "id_user_fields_add_all_link").click()
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(By.LINK_TEXT, "Bindings").click()

        # Create Stage binding for first prompt stage
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_flow").click()
        dropdown = self.driver.find_element(By.ID, "id_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-form").click()
        self.driver.find_element(By.ID, "id_stage").click()
        dropdown = self.driver.find_element(By.ID, "id_stage")
        dropdown.find_element(
            By.XPATH, '//option[. = "Stage enroll-prompt-stage-first"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").click()
        self.driver.find_element(By.ID, "id_order").send_keys("0")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Stage binding for second prompt stage
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_flow").click()
        dropdown = self.driver.find_element(By.ID, "id_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        self.driver.find_element(By.ID, "id_stage").click()
        dropdown = self.driver.find_element(By.ID, "id_stage")
        dropdown.find_element(
            By.XPATH, '//option[. = "Stage enroll-prompt-stage-second"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").click()
        self.driver.find_element(By.ID, "id_order").send_keys("1")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Stage binding for user write stage
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_flow").click()
        dropdown = self.driver.find_element(By.ID, "id_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        self.driver.find_element(By.ID, "id_stage").click()
        dropdown = self.driver.find_element(By.ID, "id_stage")
        dropdown.find_element(
            By.XPATH, '//option[. = "Stage enroll-user-write"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").click()
        self.driver.find_element(By.ID, "id_order").send_keys("2")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Stage binding for user login stage
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        dropdown = self.driver.find_element(By.ID, "id_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        dropdown = self.driver.find_element(By.ID, "id_stage")
        dropdown.find_element(
            By.XPATH, '//option[. = "Stage enroll-user-login"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").send_keys("3")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(By.CSS_SELECTOR, "[aria-label=logout]").click()

    def test_enroll_2_step(self):
        """Test 2-step enroll flow"""
        self.driver.get(self.live_server_url)
        self.setup_test_enroll_2_step()
        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "[role=enroll]"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "[role=enroll]").click()

        self.wait.until(ec.presence_of_element_located((By.ID, "id_username")))
        self.driver.find_element(By.ID, "id_username").send_keys("foo")
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password_repeat").send_keys(USER().username)
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()
        self.driver.find_element(By.ID, "id_name").send_keys("some name")
        self.driver.find_element(By.ID, "id_email").send_keys("foo@bar.baz")
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

        self.wait.until(ec.presence_of_element_located((By.LINK_TEXT, "foo")))
        self.driver.find_element(By.LINK_TEXT, "foo").click()

        self.assertEqual(
            self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").text,
            "foo",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), "foo"
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_name").get_attribute("value"),
            "some name",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_email").get_attribute("value"),
            "foo@bar.baz",
        )
