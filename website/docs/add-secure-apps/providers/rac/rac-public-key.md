---
title: RAC SSH Public Key Authentication
---

## About RAC SSH public key authentication

The RAC provider supports SSH public key authentication. This allows for secure connections to SSH endpoints without the use of passwords.

SSH private keys can be configured via several methods:

1. The settings of the RAC provider.
2. RAC endpoint settings.
3. RAC property mappings.
4. Fetched from user or group attributes via RAC property mappings.

## How to apply a private key to an RAC provider

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the **Edit** icon on the RAC provider that requires public key authentication.
4. In the **Settings** codebox enter the private key of the endpoint, for example:
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

## How to apply a private key to an RAC endpoint

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the name of the RAC provider that the endpoint belongs to.
4. Under **Endpoints**- click on the **Edit** icon next to the endpoint that requires public key authentication.
5. Under **Advanced settings**, in the **Settings** codebox enter the private key of the endpoint:
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
6. Click **Update**.

## How to apply a private key to an RAC property mapping

1.  Log in to authentik as an admin, and open the authentik Admin interface.
2.  Navigate to **Customization** > **Property Mappings** and click **Create**, then create a **RAC Provider Property Mapping** with the following settings:

        - **Name**: Choose a descriptive name
        - Under **Advanced Settings**:
          **Expression**:
          `python

    return {
    "private-key": "-----BEGIN SSH PRIVATE KEY-----
    SAMPLEgIBAAJBAKj34GkxFhD90vcNLYLInFEX6Ppy1tPf9Cnzj4p4WGeKLs1Pt8Qu
    KUpRKfFLfRYC9AIKjbJTWit+CqvjWYzvQwECAwEAAQJAIJLixBy2qpFoS4DSmoEm
    o3qGy0t6z09AIJtH+5OeRV1be+N4cDYJKffGzDa88vQENZiRm0GRq6a+HPGQMd2k
    TQIhAKMSvzIBnni7ot/OSie2TmJLY4SwTQAevXysE2RbFDYdAiEBCUEaRQnMnbp7
    9mxDXDf6AU0cN/RPBjb9qSHDcWZHGzUCIG2Es59z8ugGrDY+pxLQnwfotadxd+Uy
    v/Ow5T0q5gIJAiEAyS4RaI9YG8EWx/2w0T67ZUVAw8eOMB6BIUg0Xcu+3okCIBOs
    /5OiPgoTdSy7bcF9IGpSE8ZgGKzgYQVZeN97YE00
    -----END SSH PRIVATE KEY-----",
    }
    `

3.  Click **Finish**.
4.  Navigate to **Applications** > **Providers**.
5.  Click the **Edit** icon on the RAC provider that requires public key authentication.
6.  Under **Protocol Settings** add the newly created property mapping to **Selected Property Mappings**.
7.  Click **Update**.

## How to fetch a private key from a user's attributes and apply it to an RAC property mapping

1.  Log in to authentik as an admin, and open the authentik Admin interface.
2.  Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **RAC Provider Property Mapping** with the following settings:

        - **Name**: Choose a descriptive name
        - Under **Advanced Settings**:
          **Expression**:
          `python

    return {
    "private-key": request.user.attributes.get("<private-key-attribute-name>", "default"),
    }
    `

3.  Click **Finish**.
4.  Navigate to **Applications** > **Providers**.
5.  Click the **Edit** icon on the RAC provider that requires public key authentication.
6.  Under **Protocol Settings**, add the newly created property mapping to **Selected Property Mappings**.
7.  Click **Update**.

:::note
For group attributes, the following expression can be used `request.user.group_attributes(request.http_request)`
:::
