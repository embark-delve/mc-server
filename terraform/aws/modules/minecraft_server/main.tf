resource "aws_security_group" "minecraft" {
  name        = "${var.name_prefix}-minecraft-sg"
  description = "Allow Minecraft traffic"
  vpc_id      = var.vpc_id

  ingress {
    description = "Minecraft Server"
    from_port   = 25565
    to_port     = 25565
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-minecraft-sg"
    }
  )
}

resource "aws_instance" "minecraft" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.minecraft.id]
  subnet_id              = var.subnet_id
  
  root_block_device {
    volume_size = var.root_volume_size
    volume_type = var.root_volume_type
    encrypted   = true
  }

  user_data = <<-EOF
              #!/bin/bash
              # Install required packages
              apt-get update
              apt-get install -y docker.io docker-compose openjdk-17-jre-headless

              # Create minecraft directory
              mkdir -p /opt/minecraft/data

              # Create docker-compose.yml
              cat > /opt/minecraft/docker-compose.yml << 'COMPOSE'
              ${var.docker_compose_content}
              COMPOSE

              # Start minecraft server
              cd /opt/minecraft && docker-compose up -d

              # Setup backup cron job
              if [ "${var.enable_backups}" = "true" ]; then
                echo "0 */6 * * * cd /opt/minecraft && tar -czf /opt/minecraft/backups/minecraft_backup_\$(date +\\%Y\\%m\\%d_\\%H\\%M\\%S).tar.gz data" > /tmp/minecraft-cron
                crontab /tmp/minecraft-cron
                mkdir -p /opt/minecraft/backups
              fi
              EOF

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-minecraft-server"
    }
  )
}

# Elastic IP for the Minecraft server
resource "aws_eip" "minecraft" {
  count    = var.allocate_elastic_ip ? 1 : 0
  instance = aws_instance.minecraft.id
  domain   = "vpc"
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-minecraft-eip"
    }
  )
} 