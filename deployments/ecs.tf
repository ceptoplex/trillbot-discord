resource "aws_ssm_parameter" "discord_token" {
  name  = "/trillbot-discord/discord-token"
  type  = "SecureString"
  value = var.discord_token
}

resource "aws_ecs_task_definition" "default" {
  depends_on = [
    aws_iam_role_policy_attachment.ecs_exec_default,
    aws_iam_role_policy_attachment.ecs_exec_ssm,
    aws_iam_role_policy_attachment.ecs_exec_logging
  ]

  family = "trillbot-discord"
  requires_compatibilities = [
    "EC2"
  ]
  execution_role_arn = aws_iam_role.ecs_exec.arn
  task_role_arn      = aws_iam_role.ecs_task.arn
  container_definitions = jsonencode([
    {
      name      = "trillbot-discord"
      image     = "${aws_ecr_repository.default.repository_url}:${var.image_tag}"
      cpu       = 256
      memory    = 256
      essential = true
      secrets = [
        {
          name      = "TRILLBOT_DISCORD_TOKEN"
          valueFrom = aws_ssm_parameter.discord_token.arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-region        = "eu-central-1"
          awslogs-group         = aws_cloudwatch_log_group.default.name
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "default" {
  depends_on = [
    null_resource.image_push
  ]

  name                 = "trillbot-discord"
  cluster              = data.terraform_remote_state.trilluxe_infra.outputs.ecs_cluster_id
  task_definition      = aws_ecs_task_definition.default.arn
  desired_count        = 1
  launch_type          = "EC2"
  force_new_deployment = true
}
