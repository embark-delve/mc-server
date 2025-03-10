provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "Development"
      Project     = "Minecraft-Server"
      ManagedBy   = "Terraform"
    }
  }
}

# Use default VPC and subnet for simplicity in dev environment
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Create a key pair for SSH access
resource "aws_key_pair" "minecraft" {
  key_name   = "${var.name_prefix}-key"
  public_key = var.ssh_public_key
}

module "minecraft_server" {
  source = "../../modules/minecraft_server"

  name_prefix            = var.name_prefix
  vpc_id                 = data.aws_vpc.default.id
  subnet_id              = data.aws_subnets.default.ids[0]
  ami_id                 = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.minecraft.key_name
  allowed_cidr_blocks    = var.allowed_cidr_blocks
  allowed_ssh_cidr_blocks = var.allowed_ssh_cidr_blocks
  root_volume_size       = var.root_volume_size
  allocate_elastic_ip    = var.allocate_elastic_ip
  enable_backups         = var.enable_backups
  
  tags = {
    Environment = "dev"
    Name        = "${var.name_prefix}-server"
  }
} 