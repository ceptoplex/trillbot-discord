terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.86"
    }

    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }

  backend "s3" {
    region = "eu-central-1"
    bucket = "trilluxe-terraform-backends"
    key    = "trillbot-discord/terraform.tfstate"
  }
}

provider "aws" {
  region = "eu-central-1"
}
