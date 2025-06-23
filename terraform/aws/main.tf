provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "docs" {
  bucket = var.bucket_name
  acl    = "private"
}

variable "region" {
  default = "us-east-1"
}

variable "bucket_name" {
  default = "doc-assembler-storage"
}
