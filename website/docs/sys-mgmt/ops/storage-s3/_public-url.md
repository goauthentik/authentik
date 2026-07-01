If authentik reaches the S3 endpoint through an internal hostname but browsers must use a public hostname, set a custom domain:

```env
AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=<public_s3_domain>/<bucket_name>
```
