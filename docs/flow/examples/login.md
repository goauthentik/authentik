# Login Flow

This document describes how a simple authentication flow can be created.

This flow is created automatically when passbook is installed.

1. Create an **Identification** stage

    > Here you can select whichever fields the user can identify themselves with
    > Select the Template **Default Login**, as this template shows the (optional) Flows
    > Here you can also link optional enrollment and recovery flows.

2. Create a **Password** stage

    > Select the Backend you want the password to be checked against. Select "passbook-internal Userdatabase".

3. Create a **User Login** stage

    > This stage doesn't have any options.

4. Create a flow

    > Create a flow with the delegation of **Authentication**
    > Assign a name and a slug. The slug is used in the URL when the flow is executed.

5. Bind the stages to the flow

    > Bind the **Identification** Stage with an order of 0
    > Bind the **Password** Stage with an order of 1
    > Bind the **User Login** Stage with an order of 2

    ![](login.png)

!!! notice

    This flow can used by any user, authenticated and un-authenticated. This means any authenticated user that visits this flow can login again.
