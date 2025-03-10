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
  description = "Content of the docker-compose.yml file"
  type        = string
  default     = <<-EOT
    version: '3'
    
    services:
      minecraft:
        image: itzg/minecraft-server
        container_name: minecraft-server
        ports:
          - "25565:25565"
        environment:
          EULA: "TRUE"
          MEMORY: "2G"
          TYPE: "PAPER"
          VERSION: "1.20.4"
          ENABLE_RCON: "true"
          RCON_PASSWORD: "minecraft"
          RCON_PORT: 25575
          ALLOW_NETHER: "true"
          ENABLE_COMMAND_BLOCK: "true"
          DIFFICULTY: "normal"
          MODE: "survival"
          MOTD: "Minecraft Server - Powered by Terraform and Docker"
          SPAWN_PROTECTION: "0"
        volumes:
          - ./data:/data
        restart: unless-stopped
        tty: true
        stdin_open: true
  EOT
} 