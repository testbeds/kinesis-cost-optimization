variable "stream_name" {
  description = "Name of the Kinesis data stream to monitor"
  type        = string
}

variable "aws_region" {
  description = "AWS region the stream lives in"
  type        = string
}
