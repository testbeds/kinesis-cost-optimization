module "kinesis_stream" {
  source = "./modules/kinesis"

  stream_name = var.stream_name
  stream_mode = var.stream_mode
  shard_count = var.shard_count

  tags = {
    Project = "kinesis-cost-optimization"
  }
}

module "dashboard" {
  source = "./modules/dashboard"

  stream_name = module.kinesis_stream.stream_name
  aws_region  = var.aws_region
}
