resource "aws_kms_key" "kms" {
  description = "key"
}

resource "aws_msk_cluster" "kafka-msk" {
  cluster_name           = "kafka-msk"
  kafka_version          = "2.2.1"
  number_of_broker_nodes = 2

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    ebs_volume_size = 1
    client_subnets = [aws_subnet.backend_data[0].id, aws_subnet.backend_data[1].id]
    security_groups = [aws_security_group.msk.id]
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS_PLAINTEXT"
    }
  }

  enhanced_monitoring = "PER_TOPIC_PER_BROKER"

  tags = {
    Name = "kafka"
  }
}

output "zookeeper_connect_string" {
  value = aws_msk_cluster.kafka-msk.zookeeper_connect_string
}

output "bootstrap_brokers_tls" {
  description = "TLS connection host:port pairs"
  value       = aws_msk_cluster.kafka-msk.bootstrap_brokers_tls
}

resource "aws_security_group" "msk" {
  name        = "MSK"
  description = "Allow inbound traffic to MSK"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    security_groups = ["sg-0a809c6236a7a3b37", "sg-003bd0574cf0dca9d"]
  }

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    security_groups = ["sg-003bd0574cf0dca9d"]
  }

  ingress {
    description      = "Staging fargate"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    security_groups = ["sg-0901ce5db08017a36"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "msk"
  }
}