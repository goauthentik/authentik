#!/usr/bin/env -S bash -e

AWS_ACCESS_KEY_ID=accessKey1 AWS_SECRET_ACCESS_KEY=secretKey1 aws \
    s3api \
    --endpoint-url http://localhost:8020 \
    create-bucket \
    --acl private \
    --bucket authentik-media

AWS_ACCESS_KEY_ID=accessKey1 AWS_SECRET_ACCESS_KEY=secretKey1 aws \
    s3api \
    --endpoint-url http://localhost:8020 \
    put-bucket-cors \
    --bucket authentik-media \
    --cors-configuration \
    '{"CORSRules": [{"AllowedOrigins": ["*"], "AllowedHeaders": ["Authorization"], "AllowedMethods": ["GET"], "MaxAgeSeconds": 3000}]}'
