from authentik.endpoints.connector import BaseConnector, EnrollmentMethods


class GoogleChromeConnector(BaseConnector):

    def supported_enrollment_methods(self) -> list[EnrollmentMethods]:
        return [EnrollmentMethods.AUTOMATIC_USER]
