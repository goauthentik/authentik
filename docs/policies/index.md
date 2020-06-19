# Policies

## Kinds

There are two different kinds of policies; Standard Policy and Password Policy. Normal policies evaluate to True or False, and can be used everywhere. Password policies apply when a password is set (during user enrollment, recovery or anywhere else). These policies can be used to apply password rules such as length, complexity, etc. They can also be used to expire passwords after a certain amount of time.

## Standard Policies

---

### Reputation Policy

passbook keeps track of failed login attempts by source IP and attempted username. These values are saved as scores. Each failed login decreases the score for the client IP as well as the targeted username by 1 (one).

This policy can be used, for example, to prompt clients with a low score to pass a captcha before they can continue.

## Expression Policy

See [Expression Policy](expression.md).

## Password Policies

---

### Password Policy

This policy allows you to specify password rules, such as length and required characters.
The following rules can be set:

- Minimum amount of uppercase characters.
- Minimum amount of lowercase characters.
- Minimum amount of symbols characters.
- Minimum length.
- Symbol charset (define which characters are counted as symbols).

### Have I Been Pwned Policy

This policy checks the hashed password against the [Have I Been Pwned](https://haveibeenpwned.com/) API. This only sends the first 5 characters of the hashed password. The remaining comparison is done within passbook.

### Password-Expiry Policy

This policy can enforce regular password rotation by expiring set passwords after a finite amount of time. This forces users to set a new password.
