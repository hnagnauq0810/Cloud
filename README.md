# cloud-fastapi-deployment

Dự án mẫu hoàn chỉnh để nộp bài **Deploy FastAPI Application to AWS Cloud**.

Ứng dụng này dùng:

- **FastAPI** cho API.
- **SQLAlchemy + PostgreSQL RDS** cho database.
- **Amazon S3 + boto3** cho upload file.
- **Docker** để đóng gói app.
- **Amazon EC2** để chạy container.
- **GitHub Actions** để SSH vào EC2, pull code, build image và restart container.

> Không commit file `.env`, access key, database password, private key `.pem` lên GitHub.

---

## 1. Kiến trúc

```mermaid
flowchart LR
    GH[GitHub Actions] -- SSH deploy --> EC2[EC2 Instance]
    EC2 -- Docker build/run --> API[FastAPI Docker Container]
    API -- SQLAlchemy --> RDS[(RDS PostgreSQL)]
    API -- boto3 upload --> S3[(S3 Bucket)]
    IAM[IAM User/Policies] -. access control .-> EC2
    IAM -. access control .-> RDS
    IAM -. access control .-> S3
```

---

## 2. Cấu trúc thư mục

```text
.
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── core/config.py
│   ├── routers/
│   │   ├── health.py
│   │   ├── items.py
│   │   └── files.py
│   └── services/s3_service.py
├── aws/
│   ├── iam-policy-fastapi-deployer.json
│   └── rds-s3-security-group-notes.md
├── scripts/
│   ├── setup_ec2_ubuntu_22_04.sh
│   ├── setup_ec2_amazon_linux_2023.sh
│   ├── deploy_on_ec2.sh
│   ├── run_local.sh
│   └── test_evidence_commands.sh
├── .github/workflows/deploy.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── EVIDENCE_CHECKLIST.md
└── README.md
```

---

## 3. API endpoints

| Method | Path | Mục đích |
| --- | --- | --- |
| GET | `/` | Kiểm tra app đang chạy |
| GET | `/docs` | Swagger UI |
| GET | `/health` | Health check app |
| GET | `/health/db` | Test database connection |
| GET | `/health/s3` | Test S3 bucket access |
| POST | `/items` | Tạo item trong database |
| GET | `/items` | Lấy danh sách item |
| GET | `/items/{item_id}` | Lấy chi tiết item |
| PATCH | `/items/{item_id}` | Cập nhật item |
| DELETE | `/items/{item_id}` | Xóa item |
| POST | `/files/upload` | Upload file lên S3 và lưu metadata vào DB |
| GET | `/files` | Danh sách file đã upload |
| GET | `/files/{file_id}/presigned-url` | Tạo URL tải file tạm thời |

---

## 4. Biến môi trường

Tạo file `.env` từ mẫu:

```bash
cp .env.example .env
```

Cấu hình tối thiểu:

```env
APP_NAME=Cloud FastAPI Deployment
ENVIRONMENT=production
DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/fastapi_prod
AWS_REGION=ap-southeast-1
AWS_DEFAULT_REGION=ap-southeast-1
S3_BUCKET_NAME=fastapi-app-files-YOUR_ID
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY
```

Local smoke test có thể dùng SQLite:

```env
DATABASE_URL=sqlite:///./local.db
```

---

# PHẦN A — Chạy local để kiểm tra code

## A1. Chạy bằng Python virtual environment

```bash
cp .env.example .env
# Có thể sửa DATABASE_URL=sqlite:///./local.db để test nhanh local
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate      # Windows PowerShell
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Mở:

```text
http://localhost:8000/docs
```

Test nhanh:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title":"Local test","description":"SQLite or RDS test"}'
curl http://localhost:8000/items
```

## A2. Chạy bằng Docker local

```bash
cp .env.example .env
# Sửa .env trước khi chạy. Nếu chưa có RDS/S3, dùng DATABASE_URL=sqlite:///./local.db

docker build -t fastapi-app .
docker run -d --name fastapi-app --env-file .env -p 8000:8000 fastapi-app

docker ps
curl http://localhost:8000/health
```

Hoặc:

```bash
docker compose up --build
```

Evidence cần chụp cho Part 4:

```bash
docker build -t fastapi-app .
docker run -d --name fastapi-app --env-file .env -p 8000:8000 fastapi-app
docker ps
curl http://localhost:8000/health
```

---

# PHẦN B — Làm bài theo từng tiêu chí chấm điểm

## Part 1 — IAM Configuration, 15%

### B1.1. Tạo IAM user

Tạo IAM user tên:

```text
fastapi-deployer
```

Access type: programmatic access.

### B1.2. Attach policy

File policy mẫu nằm tại:

```text
aws/iam-policy-fastapi-deployer.json
```

Trước khi dùng, sửa `fastapi-app-files-YOUR_ID` thành bucket thật của bạn.

Có thể tạo bằng AWS CLI:

```bash
aws iam create-user --user-name fastapi-deployer

aws iam put-user-policy \
  --user-name fastapi-deployer \
  --policy-name FastAPIExamPolicy \
  --policy-document file://aws/iam-policy-fastapi-deployer.json

aws iam create-access-key --user-name fastapi-deployer
```

> Đề ghi quyền `rds:Connect`. Trong IAM policy thực tế, quyền connect bằng IAM database authentication thường là `rds-db:connect`. Nếu AWS Console báo action `rds:Connect` không hợp lệ, dùng policy mẫu trong repo này.

### B1.3. Configure AWS CLI

```bash
aws configure --profile fastapi-deployer
aws sts get-caller-identity --profile fastapi-deployer
```

Evidence cần chụp:

1. Screenshot IAM user `fastapi-deployer`.
2. Screenshot policy đã attach.
3. Screenshot terminal chạy `aws sts get-caller-identity`.

---

## Part 2 — RDS PostgreSQL, 20%

### B2.1. Tạo RDS PostgreSQL

Thông số đề bài:

| Field | Value |
| --- | --- |
| Engine | PostgreSQL 15.x |
| Instance class | db.t3.micro |
| Storage | 20 GB gp2 |
| DB instance ID | fastapi-db |
| Master username | postgres |
| Database name | fastapi_prod |
| VPC | Default VPC |
| Public accessibility | Yes, chỉ cho development/exam |
| Security Group | Allow PostgreSQL 5432 |

Security Group RDS cần inbound rule:

```text
Type: PostgreSQL
Port: 5432
Source: IP máy bạn để test local, hoặc Security Group của EC2
```

### B2.2. Cấu hình app dùng RDS

Trong `.env`:

```env
DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/fastapi_prod
```

Ví dụ endpoint RDS thường có dạng:

```text
fastapi-db.xxxxxx.ap-southeast-1.rds.amazonaws.com
```

### B2.3. Test database connection

Dùng `psql` nếu đã cài PostgreSQL client:

```bash
psql "postgresql://postgres:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/fastapi_prod" -c "select version();"
```

Hoặc chạy app rồi test:

```bash
curl http://localhost:8000/health/db
```

Tạo record trong DB:

```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"title":"RDS evidence","description":"Stored in Amazon RDS PostgreSQL"}'

curl http://localhost:8000/items
```

Evidence cần chụp:

1. Screenshot RDS instance details.
2. Screenshot Security Group có port 5432.
3. Screenshot kết nối DB thành công bằng `psql` hoặc `/health/db`.
4. Screenshot tạo/list item thành công.

---

## Part 3 — S3 File Storage, 15%

### B3.1. Tạo S3 bucket

Bucket name theo đề:

```text
fastapi-app-files-<your-id>
```

Ví dụ:

```text
fastapi-app-files-hnagnauq0810
```

Region:

```text
ap-southeast-1
```

Bật:

- Block Public Access: Enabled.
- Versioning: Enabled, optional.

AWS CLI tham khảo:

```bash
aws s3api create-bucket \
  --bucket fastapi-app-files-YOUR_ID \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1

aws s3api put-public-access-block \
  --bucket fastapi-app-files-YOUR_ID \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

aws s3api put-bucket-versioning \
  --bucket fastapi-app-files-YOUR_ID \
  --versioning-configuration Status=Enabled
```

### B3.2. Cấu hình app dùng S3

Trong `.env`:

```env
S3_BUCKET_NAME=fastapi-app-files-YOUR_ID
AWS_REGION=ap-southeast-1
AWS_DEFAULT_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY
```

### B3.3. Test upload file

Chạy app rồi test:

```bash
echo "Hello S3 evidence" > evidence.txt

curl -X POST http://localhost:8000/files/upload \
  -F "file=@evidence.txt"
```

Nếu app đang chạy trên EC2:

```bash
curl -X POST http://YOUR_EC2_PUBLIC_IP:8000/files/upload \
  -F "file=@evidence.txt"
```

Kiểm tra list file:

```bash
curl http://localhost:8000/files
```

Evidence cần chụp:

1. Screenshot bucket configuration.
2. Screenshot endpoint `/files/upload` trong Swagger.
3. Screenshot response upload thành công.
4. Screenshot object xuất hiện trong S3 bucket.

---

## Part 4 — Containerization with Docker, 15%

Các file đã có sẵn:

```text
Dockerfile
docker-compose.yml
```

Build và chạy local:

```bash
cp .env.example .env
# Sửa .env

docker build -t fastapi-app .
docker run -d --name fastapi-app --env-file .env -p 8000:8000 fastapi-app

docker ps
curl http://localhost:8000/health
```

Dừng container:

```bash
docker stop fastapi-app
docker rm fastapi-app
```

Evidence cần chụp:

1. Screenshot Dockerfile trong repo.
2. Screenshot docker-compose.yml trong repo.
3. Screenshot `docker build` thành công.
4. Screenshot `docker ps` có container `fastapi-app`.
5. Screenshot `curl http://localhost:8000/health` thành công.

---

## Part 5 — Deploy to Amazon EC2, 20%

### B5.1. Tạo EC2

Thông số đề bài:

| Field | Value |
| --- | --- |
| AMI | Ubuntu 22.04 hoặc Amazon Linux 2023 |
| Instance type | t2.micro |
| Key pair | Create or use existing |
| Security group | Allow 22, 80, 8000 |
| Storage | 8 GB gp3 |

Security Group inbound rules:

```text
SSH      22    Your IP
HTTP     80    0.0.0.0/0
Custom   8000  0.0.0.0/0
```

### B5.2. SSH vào EC2

Ubuntu:

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Amazon Linux:

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

### B5.3. Cài Docker và Git trên EC2

Ubuntu 22.04:

```bash
git clone https://github.com/YOUR_USERNAME/cloud-fastapi-deployment.git
cd cloud-fastapi-deployment
chmod +x scripts/setup_ec2_ubuntu_22_04.sh
./scripts/setup_ec2_ubuntu_22_04.sh
newgrp docker
```

Amazon Linux 2023:

```bash
git clone https://github.com/YOUR_USERNAME/cloud-fastapi-deployment.git
cd cloud-fastapi-deployment
chmod +x scripts/setup_ec2_amazon_linux_2023.sh
./scripts/setup_ec2_amazon_linux_2023.sh
newgrp docker
```

### B5.4. Tạo `.env` trên EC2

```bash
cp .env.example .env
nano .env
```

Điền giá trị thật:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@YOUR_RDS_ENDPOINT:5432/fastapi_prod
S3_BUCKET_NAME=fastapi-app-files-YOUR_ID
AWS_REGION=ap-southeast-1
AWS_DEFAULT_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY
```

### B5.5. Build và run container trên EC2

```bash
docker build -t fastapi-app .
docker run -d \
  --name fastapi-app \
  --restart unless-stopped \
  --env-file .env \
  -p 8000:8000 \
  fastapi-app
```

Hoặc dùng script:

```bash
chmod +x scripts/deploy_on_ec2.sh
./scripts/deploy_on_ec2.sh
```

Test trên EC2:

```bash
docker ps
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/s3
```

Test từ máy local/browser:

```text
http://YOUR_EC2_PUBLIC_IP:8000/docs
http://YOUR_EC2_PUBLIC_IP:8000/health
```

Evidence cần chụp:

1. Screenshot EC2 instance running.
2. Screenshot Security Group mở 22, 80, 8000.
3. Screenshot SSH terminal.
4. Screenshot `docker ps` trên EC2.
5. Screenshot `curl http://localhost:8000/health` trên EC2.
6. Screenshot browser mở `http://YOUR_EC2_PUBLIC_IP:8000/docs`.

---

## Part 6 — GitHub Actions CI/CD, 15%

Workflow đã có tại:

```text
.github/workflows/deploy.yml
```

Pipeline sẽ:

1. Chạy khi push lên branch `main`.
2. SSH vào EC2.
3. Clone repo nếu chưa có, hoặc pull/reset code mới.
4. Ghi file `.env` trên EC2 từ GitHub Secrets.
5. Build Docker image trực tiếp trên EC2.
6. Restart container `fastapi-app`.
7. Test `/health`.

### B6.1. Add GitHub Secrets

Vào GitHub repo:

```text
Settings → Secrets and variables → Actions → New repository secret
```

Thêm các secrets bắt buộc:

| Secret | Ý nghĩa |
| --- | --- |
| AWS_ACCESS_KEY_ID | Access key của IAM user |
| AWS_SECRET_ACCESS_KEY | Secret key của IAM user |
| EC2_HOST | Public IP hoặc DNS của EC2 |
| EC2_SSH_KEY | Nội dung private key `.pem` |
| DATABASE_URL | Full RDS connection string |
| S3_BUCKET_NAME | Tên S3 bucket |

Thêm secrets khuyến nghị:

| Secret | Khi nào cần |
| --- | --- |
| EC2_USER | `ubuntu` nếu Ubuntu, `ec2-user` nếu Amazon Linux. Workflow default là `ubuntu` nếu không set. |
| AWS_DEFAULT_REGION | `ap-southeast-1` |

### B6.2. Chuẩn bị repo trên EC2

Nếu repo private, bạn cần cấu hình EC2 có quyền pull repo, ví dụ dùng GitHub Deploy Key hoặc chuyển repo tạm sang public cho bài thi.

Nếu repo public, workflow có thể clone bằng HTTPS:

```bash
git clone https://github.com/YOUR_USERNAME/cloud-fastapi-deployment.git
```

### B6.3. Trigger pipeline

Commit và push:

```bash
git add .
git commit -m "Complete AWS FastAPI deployment exam"
git push origin main
```

Vào tab:

```text
GitHub repo → Actions → Deploy FastAPI to EC2
```

Evidence cần chụp:

1. Screenshot file `.github/workflows/deploy.yml` trong repo.
2. Screenshot GitHub Secrets, chỉ cần thấy tên secret, không cần lộ value.
3. Screenshot workflow run màu xanh/success.
4. Screenshot log đoạn SSH deploy, docker build, docker run, curl `/health`.
5. Screenshot browser mở API sau khi workflow chạy.

---

# PHẦN C — Lệnh test evidence nhanh

Sau khi app chạy, có thể dùng script:

```bash
chmod +x scripts/test_evidence_commands.sh
BASE_URL=http://YOUR_EC2_PUBLIC_IP:8000 ./scripts/test_evidence_commands.sh
```

Hoặc local:

```bash
BASE_URL=http://localhost:8000 ./scripts/test_evidence_commands.sh
```

Script này test:

- `/`
- `/health`
- `/health/db`
- tạo item trong DB
- list item
- `/health/s3`
- upload file lên S3

---

# PHẦN D — Troubleshooting

## 1. Không truy cập được `http://EC2_IP:8000/docs`

Kiểm tra:

```bash
sudo systemctl status docker
docker ps
docker logs fastapi-app
```

Security Group EC2 phải mở inbound port `8000`.

## 2. `/health/db` lỗi

Kiểm tra:

- `DATABASE_URL` đúng chưa.
- RDS endpoint đúng chưa.
- RDS public accessibility là Yes cho bài exam.
- RDS Security Group mở port `5432` từ EC2 Security Group hoặc IP của bạn.
- Username/password đúng chưa.

Test từ EC2:

```bash
docker exec -it fastapi-app env | grep DATABASE_URL
```

## 3. Upload S3 lỗi AccessDenied

Kiểm tra:

- `S3_BUCKET_NAME` đúng chưa.
- IAM policy có đúng bucket ARN chưa.
- Access key/secret key có đúng user `fastapi-deployer` không.
- Bucket ở region `ap-southeast-1` không.

Test:

```bash
aws s3 ls s3://fastapi-app-files-YOUR_ID --region ap-southeast-1
```

## 4. GitHub Actions SSH lỗi

Kiểm tra:

- `EC2_HOST` là public IP/DNS đúng.
- `EC2_USER` đúng: Ubuntu dùng `ubuntu`, Amazon Linux dùng `ec2-user`.
- `EC2_SSH_KEY` chứa toàn bộ private key, gồm cả dòng `-----BEGIN...` và `-----END...`.
- EC2 Security Group mở port `22` cho GitHub runner. Cho bài exam có thể mở tạm `0.0.0.0/0`, sau đó đóng lại.

## 5. GitHub Actions pull repo lỗi

Nếu repo private, EC2 không tự pull được bằng HTTPS public. Cách xử lý:

- Tạm để repo public trong thời gian nộp bài, hoặc
- Cấu hình GitHub Deploy Key trên EC2, hoặc
- Dùng Personal Access Token an toàn qua secret riêng.

---

# PHẦN E — Checklist nộp bài

Xem file:

```text
EVIDENCE_CHECKLIST.md
```

Nên tạo thư mục evidence trong repo hoặc trong file nộp riêng:

```text
evidence/
├── part1-iam-user.png
├── part1-policy.png
├── part1-sts.png
├── part2-rds-details.png
├── part2-db-connection.png
├── part3-s3-bucket.png
├── part3-upload-success.png
├── part4-docker-build.png
├── part4-docker-ps.png
├── part5-ec2-running.png
├── part5-security-group.png
├── part5-api-response.png
├── part6-secrets.png
├── part6-workflow-success.png
└── part6-auto-deploy-result.png
```
