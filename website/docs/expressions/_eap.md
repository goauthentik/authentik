:::warning Use of trusted Certificate Authority
For EAP-TLS, note that you should NOT use a globally known CA.
For example, using a Verisign cert as a "known CA" means that ANYONE who has a certificate signed by them can authenticate via EAP-TLS. Using private PKI certificates that are trusted by the end-device is best practise to distribute client certificates.
:::
