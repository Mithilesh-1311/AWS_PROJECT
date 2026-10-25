# Deployment and operations

Status on 2026-10-26: **prepared**, Terraform **validated** with a mocked-provider security plan; **not deployed**, **not cloud-verified**. Native Caddy authenticated static/API/WebSocket smoke passed locally. Docker, AWS CLI/account authorization, a domain and an approved budget were unavailable, so no container runtime or cloud resource creation is claimed.

## Local containers

Install Docker with Compose. From the project root:

```powershell
Copy-Item .env.example .env
docker run --rm caddy:2.10.2-alpine caddy hash-password
python -c "import secrets; print(secrets.token_hex(32))"
```

Put the generated hash/token in `.env`; do not commit them. Single-quote the bcrypt hash to preserve dollar signs. Set the dataset path. On Linux, create `backend/artifacts` and give UID 10001 write access (`sudo chown -R 10001:10001 backend/artifacts`). Raw data is mounted read-only. Then:

```powershell
docker compose config --quiet
docker compose up -d --build --wait
```

Visit http://localhost:8080 and authenticate. The API and worker have no published host ports. Without raw data/model, health can pass while dataset/model readiness remains unavailable. Train/activate through the backend container as documented in EXPERIMENTS.md. Test real inference and recorded replay after restoring compatible artifacts or training. HTTP basic auth is for loopback testing only; cloud access requires HTTPS.

## AWS resources and prerequisites

`infra/terraform/main.tf.json` is the single IaC implementation. It creates one VPC/public subnet/route/IGW, one configurable EC2 host/EIP, restricted HTTPS ingress plus public port 80 for ACME challenge/redirect, encrypted gp3 EBS, SSM instance access, a private versioned S3 bucket and CloudWatch logs (14-day retention) / host metrics. SSH and API ports are not opened. IAM grants only required storage prefixes, runtime parameter read and telemetry, plus AWS's SSM core managed policy. IMDSv2 is mandatory. The instance role contains no static access keys.

Defaults are ap-south-1, t3.large and 100 GiB EBS. These are configuration defaults, not an approved purchase or a free-tier claim. Estimate EC2 hours/CPU credits, EBS (including retained volumes), EIP/public IPv4, S3 versions/requests, CloudWatch ingestion/storage, transfer and domain costs in the chosen region before apply. Training and serving have different resource needs; the CPU course host has no GPU provisioned.

Provide account credentials through an approved role/profile, exact researcher CIDRs, region, budget, a DNS name pointing at the EIP, dataset-storage permission and an immutable release SHA256. Store runtime configuration as an SSM SecureString named `/eog-intent/runtime-env` (or configure its name). Its value is a dotenv file, not Terraform variables:

```dotenv
EOG_SITE=eog.example.org
EOG_ALLOWED_ORIGINS=https://eog.example.org
EOG_HTTP_BIND=127.0.0.1:8080
EOG_ACME_BIND=0.0.0.0:80
EOG_HTTPS_BIND=0.0.0.0:443
EOG_DATASET_PATH=/data/eog
EOG_USER=researcher
EOG_PASSWORD_HASH='$2a$REPLACE_WITH_REAL_BCRYPT_HASH'
EOG_PROXY_TOKEN=REPLACE_WITH_RANDOM_64_HEX_CHARACTERS
AWS_REGION=ap-south-1
EOG_LOG_GROUP=/eog-intent/containers
```

Use the AWS-managed SSM encryption key with the supplied role policy. A customer-managed KMS key requires an additional reviewed decrypt policy. Runtime secrets are fetched on-host with restrictive file permissions; they are not placed in images, user-data or Terraform state. Keep state private because it still contains infrastructure identifiers. All authenticated researchers share one role; use a stronger identity/role system before multi-tenant use.

## Review, provision and start

1. Run `git archive --format=tar.gz --output=release.tar.gz HEAD` and compute its SHA256. Copy `terraform.tfvars.example` to a private `terraform.tfvars`; replace CIDR, release key and checksum. Never use the placeholder address/checksum for a real apply.
2. From `infra/terraform`, run `terraform init`, `terraform validate`, `terraform test`, then `terraform plan -out=reviewed.tfplan`. Review actual account, region, replacements and cost assumptions. **No real-account plan or apply was run in this session.** Apply only the approved concrete plan with `terraform apply reviewed.tfplan`.
3. Upload the exact reviewed archive to the output bucket under `releases/<commit>.tar.gz`, and provision the runtime SecureString. Bootstrap installs Docker/Compose and CloudWatch and enables the service, but deliberately does not start it before these inputs exist.
4. Stage authorized recordings under `/data/eog/S1...S14` through SSM. Verify each object against the published per-file SHA256, then run `python -m scripts.verify_artifacts` in the API container. Restore compatible generated artifacts or train a new serving model. No raw-data transfer is automated by Terraform or CI.
5. Use `aws ssm start-session --target <instance-id> --region <region>`, then `sudo systemctl start eog`. Check `systemctl status eog`, `docker compose ps`, authenticated `/api/ready`, inference, replay, exports, worker logs and CloudWatch. Confirm HTTPS certificate validity from an allowed researcher address. Only then label the deployment cloud-verified.

Bootstrap verifies release SHA256 before extraction. Compose's binary is pinned and checksum-verified. The native proxy smoke script is `python ops/smoke_proxy.py` with `CADDY_BIN` set if needed; it requires actual data/model and a built frontend. It starts temporary local processes and checks unauthenticated/forged-header denial, authenticated routes and matching HTTP/WS scores. It does not replace a container or cloud smoke test.

## CI, updates and recovery

`verify.yml` checks backend, frontend, audits, Terraform/mock plan and container health/auth on GitHub Actions. Its browser boundary test uses explicit fixtures; full real-data browser tests run locally because Git contains no dataset. GitHub Actions has not run until this commit is pushed and the workflow result is observed.

`release.yml` is manual-only and uses OIDC with environment `aws-release`. Configure AWS_RELEASE_ROLE_ARN, AWS_REGION and AWS_RELEASE_BUCKET as environment variables; require environment approval. The AWS trust policy must restrict `aud=sts.amazonaws.com` and `sub=repo:Mithilesh-1311/AWS_PROJECT:environment:aws-release`. Grant that release role only PutObject under the specific bucket's `releases/*` prefix. The workflow publishes an archive/checksum and performs no apply or SSM command. Do not configure long-lived repository access keys.

For an update, back up state/artifacts, stop the worker, stage the reviewed commit archive/checksum and update the deployment configuration. Changing Terraform user-data currently replaces the EC2 instance: inspect that replacement plan before applying. Restore retained storage/backups explicitly; the system does not claim automatic state migration. Alternatively update the existing host over SSM using the same checksum-verified release procedure. Rebuild/restart Compose and rerun smoke checks. Roll back to a previous reviewed release and matching artifact versions; never load an older incompatible pickle in a newer sklearn runtime.

For backup, stop the worker so no experiment is writing. Use SQLite's backup API for the job database (plain copying an active WAL database is unsafe), then archive the snapshot, active-model JSON and immutable experiment/model folders. Upload only derived artifacts/backups to private versioned prefixes. Test restore into a separate directory before replacing host state; verify hashes, versions, readiness and a known prediction. Dataset backup requires its own permission. Cache can be rebuilt.

There is one host and one local SQLite queue: downtime and host loss are expected availability risks. EBS root storage is intentionally retained on termination; it continues costing money. Versioned S3 objects and retained CloudWatch data also survive some resource changes. For teardown, first export/verify backups, review a `terraform plan -destroy`, then obtain approval before `terraform destroy`. Never automatically delete the bucket, retained volumes or backups. Private `*.tfvars`, state, plans and secrets are ignored by Git.
