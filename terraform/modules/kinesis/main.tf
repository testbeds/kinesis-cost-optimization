resource "aws_kinesis_stream" "this" {
  name             = var.stream_name
  retention_period = var.retention_period

  # shard_count is only meaningful in PROVISIONED mode; Terraform ignores it
  # for ON_DEMAND streams but AWS requires the field to be omitted or left
  # consistent, so we only set it when in PROVISIONED mode.
  shard_count = var.stream_mode == "PROVISIONED" ? var.shard_count : null

  stream_mode_details {
    stream_mode = var.stream_mode
  }

  tags = var.tags
}
