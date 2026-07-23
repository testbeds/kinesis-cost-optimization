resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = "${var.stream_name}-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Incoming Throughput"
          region = var.aws_region
          period = 60
          stat   = "Sum"
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", "StreamName", var.stream_name, { yAxis = "left" }],
            ["AWS/Kinesis", "IncomingBytes", "StreamName", var.stream_name, { yAxis = "right" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Write Throttling (Failures)"
          region = var.aws_region
          period = 60
          stat   = "Sum"
          metrics = [
            ["AWS/Kinesis", "WriteProvisionedThroughputExceeded", "StreamName", var.stream_name, { color = "#d62728" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "PutRecords Success / Latency"
          region = var.aws_region
          period = 60
          metrics = [
            ["AWS/Kinesis", "PutRecords.Success", "StreamName", var.stream_name, { stat = "Average", yAxis = "left" }],
            ["AWS/Kinesis", "PutRecords.Latency", "StreamName", var.stream_name, { stat = "Average", yAxis = "right" }],
          ]
        }
      },
    ]
  })
}
