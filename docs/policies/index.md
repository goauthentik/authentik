# Policies

## Kinds

There are two different Kind of policies, a Standard Policy and a Password Policy. Normal Policies just evaluate to True or False, and can be used everywhere. Password Policies apply when a Password is set (during User enrollment, Recovery or anywhere else). These policies can be used to apply Password Rules like length, etc. The can also be used to expire passwords after a certain amount of time.

## Standard Policies

---

### Group-Membership Policy

This policy evaluates to True if the current user is a Member of the selected group.

### Reputation Policy

passbook keeps track of failed login attempts by Source IP and Attempted Username. These values are saved as scores. Each failed login decreases the Score for the Client IP as well as the targeted Username by one.

This policy can be used to for example prompt Clients with a low score to pass a Captcha before they can continue.

## Expression Policy

See [Expression Policy](expression/index.md).

### Webhook Policy

This policy allows you to send an arbitrary HTTP Request to any URL. You can then use JSONPath to extract the result you need.

## Password Policies

---

### Password Policy

This Policy allows you to specify Password rules, like Length and required Characters.
The following rules can be set:

-   Minimum amount of Uppercase Characters
-   Minimum amount of Lowercase Characters
-   Minimum amount of Symbols Characters
-   Minimum Length
-   Symbol charset (define which characters are counted as symbols)

### Have I Been Pwned Policy

This Policy checks the hashed Password against the [Have I Been Pwned](https://haveibeenpwned.com/) API. This only sends the first 5 characters of the hashed password. The remaining comparison is done within passbook.

### Password-Expiry Policy

This policy can enforce regular password rotation by expiring set Passwords after a finite amount of time. This forces users to set a new password.
