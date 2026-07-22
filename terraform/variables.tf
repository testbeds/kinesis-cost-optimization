variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "stream_name" {
  description = "Name of the Kinesis data stream"
  type        = string
  default     = "kinesis-cost-optimization"
}

variable "stream_mode" {
  description = "Capacity mode for the stream: PROVISIONED or ON_DEMAND"
  type        = string
  default     = "PROVISIONED"
}

variable "shard_count" {
  description = "Number of shards (only used when stream_mode is PROVISIONED)"
  type        = number
  default     = 1
}
