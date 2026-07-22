terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # bucket/key/region are supplied at init time via -backend-config
  # (see scripts/create-tf-backend-bucket.sh and terraform-cd.yml)
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}
