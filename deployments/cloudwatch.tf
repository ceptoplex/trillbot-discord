resource "aws_cloudwatch_log_group" "default" {
  name              = "/ecs/trillbot-discord"
  retention_in_days = 365
}
