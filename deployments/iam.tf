
data "aws_iam_policy_document" "ecs_roles" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_exec" {
  name_prefix        = "ecs-exec-trillbot-discord-"
  assume_role_policy = data.aws_iam_policy_document.ecs_roles.json
}

resource "aws_iam_role" "ecs_task" {
  name_prefix        = "ecs-task-trillbot-discord-"
  assume_role_policy = data.aws_iam_policy_document.ecs_roles.json
}

resource "aws_iam_role_policy_attachment" "ecs_exec_default" {
  role       = aws_iam_role.ecs_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_policy" "ecs_exec_ssm" {
  name = "ecs-trillbot-discord-ssm"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "ssm:GetParameters",
        Resource = "arn:aws:ssm:eu-central-1:528655409007:parameter/trillbot-discord/discord-token"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec_ssm" {
  role       = aws_iam_role.ecs_exec.name
  policy_arn = aws_iam_policy.ecs_exec_ssm.arn
}

resource "aws_iam_policy" "ecs_exec_logging" {
  name = "ecs-trillbot-discord-logging"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = aws_cloudwatch_log_group.default.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec_logging" {
  role       = aws_iam_role.ecs_exec.name
  policy_arn = aws_iam_policy.ecs_exec_logging.arn
}
