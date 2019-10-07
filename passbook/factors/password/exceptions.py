"""passbook password policy exceptions"""

class PasswordPolicyInvalid(Exception):
    """Exception raised when a Password Policy fails"""

    messages = []

    def __init__(self, *messages):
        super().__init__()
        self.messages = messages
