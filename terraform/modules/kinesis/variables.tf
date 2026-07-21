variable "stream_name" {
  description = "Name of the Kinesis data stream"
  type        = string
}

variable "stream_mode" {
  description = "Capacity mode for the stream: PROVISIONED or ON_DEMAND"
  type        = string
  default     = "PROVISIONED"

  validation {
    condition     = contains(["PROVISIONED", "ON_DEMAND"], var.stream_mode)
    error_message = "stream_mode must be either PROVISIONED or ON_DEMAND."
  }
}

variable "shard_count" {
  description = "Number of shards (only used when stream_mode is PROVISIONED)"
  type        = number
  default     = 1
}

variable "retention_period" {
  description = "Data retention period in hours"
  type        = number
  default     = 24
}

variable "tags" {
  description = "Tags to apply to the stream"
  type        = map(string)
  default     = {}
}
