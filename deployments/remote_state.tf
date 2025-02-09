data "terraform_remote_state" "trilluxe_infra" {
  backend = "s3"
  config = {
    region = "eu-central-1"
    bucket = "trilluxe-terraform-backends"
    key    = "trilluxe-infra/terraform.tfstate"
  }
}
