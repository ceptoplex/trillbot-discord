resource "aws_ecr_repository" "default" {
  name         = "trillbot-discord"
  force_delete = true
}

resource "aws_ecr_lifecycle_policy" "default" {
  repository = aws_ecr_repository.default.name
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only last 5 tagged images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

data "aws_ecr_authorization_token" "default" {}

resource "null_resource" "image_push" {
  triggers = {
    local_exec_version = "1" # Change this if the script below changes.
    image              = "${aws_ecr_repository.default.repository_url}:${var.image_tag}"
  }

  provisioner "local-exec" {
    command = <<EOT
      docker login --username ${data.aws_ecr_authorization_token.default.user_name} --password ${data.aws_ecr_authorization_token.default.password} ${aws_ecr_repository.default.repository_url}
      docker tag trillbot-discord:${var.image_tag} ${aws_ecr_repository.default.repository_url}:${var.image_tag}
      docker push ${aws_ecr_repository.default.repository_url}:${var.image_tag}
    EOT
  }
}
