output "stream_name" {
  value = aws_kinesis_stream.this.name
}

output "stream_arn" {
  value = aws_kinesis_stream.this.arn
}

output "stream_mode" {
  value = aws_kinesis_stream.this.stream_mode_details[0].stream_mode
}

output "shard_count" {
  value = aws_kinesis_stream.this.shard_count
}
