# Factors

A factor represents a single authenticating factor for a user. Common examples of this would be a password or an OTP. These factors can be combined in any order, and can be dynamically enabled using policies.

## Password Factor

This is the standard Password Factor. It allows you to select which Backend the password is checked with. here you can also specify which Policies are used to check the password. You can also specify which Factors a User has to pass to recover their account.

## Dummy Factor

This factor waits a random amount of time. Mostly used for debugging.

## E-Mail Factor

This factor is mostly for recovery, and used in conjunction with the Password Factor.

## OTP Factor

This is your typical One-Time Password implementation, compatible with Authy and Google Authenticator. You can enfore this Factor so that every user has to configure it, or leave it optional.

## Captcha Factor

While this factor doesn't really authenticate a user, it is part of the Authentication Flow. passbook uses Google's reCaptcha implementation.
