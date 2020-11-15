---
title: Upgrading to 0.9
---

Due to some database changes that had to be rather sooner than later, there is no possibility to directly upgrade. You must extract the data before hand and import it again. It is recommended to spin up a second instance of passbook to do this.

To export data from your old instance, run this command:

- docker-compose
```
docker-compose exec server ./manage.py dumpdata -o /tmp/passbook_dump.json passbook_core.User passbook_core.Group passbook_crypto.CertificateKeyPair passbook_audit.Event otp_totp.totpdevice otp_static.staticdevice otp_static.statictoken
docker cp passbook_server_1:/tmp/passbook_dump.json passbook_dump.json
```

- kubernetes
```
kubectl exec -it passbook-web-... -- ./manage.py dumpdata -o /tmp/passbook_dump.json passbook_core.User passbook_core.Group passbook_crypto.CertificateKeyPair passbook_audit.Event otp_totp.totpdevice otp_static.staticdevice otp_static.statictoken
kubectl cp passbook-web-...:/tmp/passbook_dump.json passbook_dump.json
```

After that, create a new passbook instance in a different namespace (kubernetes) or in a different folder (docker-compose). Once this instance is running, you can use the following commands to restore the data. On docker-compose, you still have to run the `migrate` command, to create all database structures.

- docker-compose
```
docker cp passbook_dump.json new_passbook_server_1:/tmp/passbook_dump.json
docker-compose exec server ./manage.py loaddata /tmp/passbook_dump.json
```

- kubernetes
```
kubectl cp passbook_dump.json passbook-web-...:/tmp/passbook_dump.json
kubectl exec -it passbook-web-... -- ./manage.py loaddata /tmp/passbook_dump.json
```

Now, you should be able to login to the new passbook instance, and migrate the rest of the data over.
