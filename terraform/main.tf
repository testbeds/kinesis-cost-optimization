module "kinesis_stream" {
  source = "./modules/kinesis"

  stream_name = var.stream_name
  stream_mode = var.stream_mode
  shard_count = var.shard_count

  tags = {
    Project = "kinesis-cost-optimization"
  }
}
