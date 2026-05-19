# Evidence Checklist theo rubric chấm điểm

Dùng checklist này để chụp và gom ảnh nộp bài.

---

## Part 1 — IAM Configuration, 15%

- [ ] Screenshot IAM user `fastapi-deployer` đã được tạo.
- [ ] Screenshot permissions/policy đã attach cho user.
- [ ] Screenshot terminal chạy:

```bash
aws sts get-caller-identity --profile fastapi-deployer
```

Tên file gợi ý:

```text
part1-iam-user.png
part1-policy.png
part1-sts-get-caller-identity.png
```

---

## Part 2 — RDS PostgreSQL, 20%

- [ ] Screenshot RDS instance `fastapi-db` ở trạng thái Available.
- [ ] Screenshot RDS details có engine PostgreSQL, endpoint, database name.
- [ ] Screenshot Security Group cho phép PostgreSQL port 5432.
- [ ] Screenshot kết nối DB thành công bằng một trong các lệnh:

```bash
psql "postgresql://postgres:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/fastapi_prod" -c "select version();"
```

hoặc:

```bash
curl http://localhost:8000/health/db
```

- [ ] Screenshot tạo/list item để chứng minh app dùng DB:

```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title":"RDS evidence","description":"Stored in Amazon RDS"}'

curl http://localhost:8000/items
```

Tên file gợi ý:

```text
part2-rds-details.png
part2-rds-security-group.png
part2-db-connection.png
part2-create-item.png
```

---

## Part 3 — S3 File Storage, 15%

- [ ] Screenshot S3 bucket `fastapi-app-files-<your-id>`.
- [ ] Screenshot Block Public Access enabled.
- [ ] Screenshot endpoint `/files/upload` trong Swagger UI.
- [ ] Screenshot upload file thành công:

```bash
echo "Hello evidence" > evidence.txt
curl -X POST http://localhost:8000/files/upload -F "file=@evidence.txt"
```

- [ ] Screenshot object mới xuất hiện trong S3 bucket.

Tên file gợi ý:

```text
part3-s3-bucket.png
part3-s3-block-public-access.png
part3-upload-endpoint.png
part3-upload-response.png
part3-s3-object.png
```

---

## Part 4 — Docker, 15%

- [ ] Screenshot `Dockerfile` trong GitHub repo.
- [ ] Screenshot `docker-compose.yml` trong GitHub repo.
- [ ] Screenshot build thành công:

```bash
docker build -t fastapi-app .
```

- [ ] Screenshot container running:

```bash
docker run -d --name fastapi-app --env-file .env -p 8000:8000 fastapi-app
docker ps
```

- [ ] Screenshot API response local:

```bash
curl http://localhost:8000/health
```

Tên file gợi ý:

```text
part4-dockerfile.png
part4-docker-compose.png
part4-docker-build.png
part4-docker-ps.png
part4-local-api-health.png
```

---

## Part 5 — EC2 Deployment, 20%

- [ ] Screenshot EC2 instance running.
- [ ] Screenshot EC2 Security Group inbound rules: 22, 80, 8000.
- [ ] Screenshot SSH vào EC2 thành công.
- [ ] Screenshot cài Docker/Git thành công:

```bash
docker --version
git --version
```

- [ ] Screenshot container chạy trên EC2:

```bash
docker ps
```

- [ ] Screenshot API response từ EC2:

```bash
curl http://localhost:8000/health
curl http://YOUR_EC2_PUBLIC_IP:8000/health
```

- [ ] Screenshot browser mở:

```text
http://YOUR_EC2_PUBLIC_IP:8000/docs
```

Tên file gợi ý:

```text
part5-ec2-running.png
part5-security-group.png
part5-ssh.png
part5-docker-version.png
part5-docker-ps.png
part5-api-health.png
part5-swagger-docs.png
```

---

## Part 6 — GitHub Actions CI/CD, 15%

- [ ] Screenshot file `.github/workflows/deploy.yml` trong GitHub repo.
- [ ] Screenshot GitHub Secrets names:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `EC2_HOST`
  - `EC2_SSH_KEY`
  - `DATABASE_URL`
  - `S3_BUCKET_NAME`
  - `EC2_USER`, nếu dùng Amazon Linux hoặc muốn rõ ràng.
  - `AWS_DEFAULT_REGION`, nên set là `ap-southeast-1`.
- [ ] Screenshot workflow run success.
- [ ] Screenshot log có các bước:
  - SSH vào EC2.
  - `git fetch`/`git reset`.
  - `docker build`.
  - `docker run`.
  - `curl http://localhost:8000/health`.
- [ ] Screenshot API sau khi push code mới.

Tên file gợi ý:

```text
part6-deploy-yml.png
part6-github-secrets.png
part6-workflow-success.png
part6-workflow-log.png
part6-auto-deploy-api.png
```

---

## Required Deliverables tổng hợp

- [ ] Source code hoàn chỉnh đã commit lên GitHub.
- [ ] `Dockerfile`.
- [ ] `docker-compose.yml`.
- [ ] `.github/workflows/deploy.yml`.
- [ ] `README.md` đầy đủ.
- [ ] Screenshots evidence cho đủ 6 phần.
- [ ] App chạy được trên EC2.
- [ ] Các endpoint chính hoạt động:
  - [ ] `/health`
  - [ ] `/health/db`
  - [ ] `/health/s3`
  - [ ] `/items`
  - [ ] `/files/upload`
- [ ] CI/CD chạy thành công sau khi push lên `main`.

---

## Gợi ý thứ tự chụp evidence

1. Chụp IAM trước khi chuyển sang RDS.
2. Chụp RDS instance và Security Group ngay sau khi tạo.
3. Chụp S3 bucket và upload test.
4. Chụp Docker build/run local.
5. Chụp EC2 running, SG, SSH, docker ps, API public IP.
6. Chụp GitHub Secrets và Actions success cuối cùng.
