# Security Group Notes

## EC2 Security Group
Open inbound rules:

| Type | Port | Source | Evidence |
| --- | --- | --- | --- |
| SSH | 22 | Your IP only | Screenshot required |
| HTTP | 80 | 0.0.0.0/0 | Screenshot required |
| Custom TCP | 8000 | 0.0.0.0/0 for exam testing | Screenshot required |

## RDS Security Group
Open inbound rule:

| Type | Port | Source | Evidence |
| --- | --- | --- | --- |
| PostgreSQL | 5432 | EC2 security group, or your IP for local testing | Screenshot required |

For the exam, public RDS is accepted for development. For production, keep RDS in private subnets.
