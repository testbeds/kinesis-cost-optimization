output "stream_name" {
  value = module.kinesis_stream.stream_name
}

output "stream_arn" {
  value = module.kinesis_stream.stream_arn
}

output "stream_mode" {
  value = module.kinesis_stream.stream_mode
}

output "shard_count" {
  value = module.kinesis_stream.shard_count
}

output "dashboard_url" {
  value = module.dashboard.dashboard_url
}
