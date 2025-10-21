:::warning Use of trusted Certificate Authority

- For EAP-TLS, note that you should NOT use a globally known CA.

Using private PKI certificates that are trusted by the end-device is best practise. For example, using a Verisign certificate as a "known CA" means that ANYONE who has a certificate signed by them can authenticate via EAP-TLS, and in addition you should implement [custom validation](https://docs.goauthentik.io/add-secure-apps/flows-stages/flow/context/#auth_method-string) to prevent unauthorized access.
:::
