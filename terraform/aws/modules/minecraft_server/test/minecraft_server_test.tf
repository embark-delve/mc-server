terraform {
  required_providers {
    test = {
      source = "terraform.io/builtin/test"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
  # Use mock credentials for tests or environment variables
  skip_credentials_validation = true
  skip_requesting_account_id  = true
}

module "main" {
  source = "../"
  
  # Required variables with test values
  name_prefix = "test-minecraft"
  vpc_id      = "vpc-12345678"
  subnet_id   = "subnet-12345678"
  ami_id      = "ami-12345678"
  key_name    = "test-key"
  
  # Optional variables with non-default values for testing
  instance_type          = "t3.small"
  allowed_cidr_blocks    = ["10.0.0.0/8"]
  allowed_ssh_cidr_blocks = ["10.0.0.0/16"]
  root_volume_size       = 30
  allocate_elastic_ip    = false
  enable_backups         = false
}

# Test that the security group is created with the correct name
resource "test_assertions" "security_group" {
  component = "security_group"
  
  equal "name" {
    description = "Security group name includes the prefix"
    got         = aws_security_group.minecraft.name
    want        = "${var.name_prefix}-minecraft-sg"
  }
}

# Test that an EC2 instance is created with the right instance type
resource "test_assertions" "instance" {
  component = "instance"
  
  equal "instance_type" {
    description = "Instance type is correctly set"
    got         = aws_instance.minecraft.instance_type
    want        = var.instance_type
  }
  
  equal "volume_size" {
    description = "Root volume size is correctly set"
    got         = aws_instance.minecraft.root_block_device[0].volume_size
    want        = var.root_volume_size
  }
} 