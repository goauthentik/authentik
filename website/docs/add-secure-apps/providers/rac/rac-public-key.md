---
title: RAC Public Key Authentication
---

## About RAC public key authentication

The RAC provider supports public key authentication. This allows for secure connections to endpoints without the use of username and passwords.

## Current limitations

Each RAC provider is limited to a single private key. This means that a RAC provider with a private key set, will utilize that private key for all connections.

## How to apply an SSH private key to an RAC provider

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the **Edit** icon on the RAC provider that requires SSH public key authentication.
4. In the **Settings** codebox enter the SSH private key of the endpoint, for example:
    ```python
    private-key:
        -----BEGIN SSH PRIVATE KEY-----
        SAMPLEgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKLs1Pt8Qu
        KUpRKfFLfRYC9AIKjbJTWit+CqvjWYzvQwECAwEAAQJAIJLixBy2qpFoS4DSmoEm
        o3qGy0t6z09AIJtH+5OeRV1be+N4cDYJKffGzDa88vQENZiRm0GRq6a+HPGQMd2k
        TQIhAKMSvzIBnni7ot/OSie2TmJLY4SwTQAevXysE2RbFDYdAiEBCUEaRQnMnbp7
        9mxDXDf6AU0cN/RPBjb9qSHDcWZHGzUCIG2Es59z8ugGrDY+pxLQnwfotadxd+Uy
        v/Ow5T0q5gIJAiEAyS4RaI9YG8EWx/2w0T67ZUVAw8eOMB6BIUg0Xcu+3okCIBOs
        /5OiPgoTdSy7bcF9IGpSE8ZgGKzgYQVZeN97YE00
        -----END SSH PRIVATE KEY-----
    ```
5. Click **Update**.
