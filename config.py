import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "sda_secret_key")

    # RDS database URL (MySQL example)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
