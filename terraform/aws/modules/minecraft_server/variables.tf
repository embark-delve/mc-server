variable "name_prefix" {
  description = "Prefix to use for resource naming"
  type        = string
  default     = "minecraft"
}

variable "vpc_id" {
  description = "ID of the VPC where resources will be created"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet where the EC2 instance will be launched"
  type        = string
}

variable "ami_id" {
  description = "AMI ID to use for the EC2 instance (Ubuntu recommended)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "Name of the SSH key pair to use for the EC2 instance"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to connect to the Minecraft server"
  type        = list(string)
  default     = []
}

variable "allowed_ssh_cidr_blocks" {
  description = "CIDR blocks allowed to connect via SSH"
  type        = list(string)
  default     = []
}

variable "root_volume_size" {
  description = "Size of the root volume in GB"
  type        = number
  default     = 20
}

variable "root_volume_type" {
  description = "Type of the root volume"
  type        = string
  default     = "gp3"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
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

variable "docker_compose_content" {
  description = "Explicit reviewed Compose configuration, including private secrets and EULA choice"
  type = string
  default = ""
  sensitive = true
}

variable "cloud_deployment_reviewed" {
  description = "Legacy cloud deployment is disabled pending a separate security review"
  type = bool
  default = false
}
