variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-west-2"
}

variable "name_prefix" {
  description = "Prefix to use for resource naming"
  type        = string
  default     = "minecraft-dev"
}

variable "ssh_public_key" {
  description = "SSH public key for accessing the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to connect to the Minecraft server"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_ssh_cidr_blocks" {
  description = "CIDR blocks allowed to connect via SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "root_volume_size" {
  description = "Size of the root volume in GB"
  type        = number
  default     = 20
}

variable "allocate_elastic_ip" {
  description = "Whether to allocate an Elastic IP for the server"
  type        = bool
  default     = true
}

variable "enable_backups" {
  description = "Whether to enable automated backups"
  type        = bool
  default     = true
} 