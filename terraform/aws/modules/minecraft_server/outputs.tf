output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.minecraft.id
}

output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.minecraft.public_ip
}

output "elastic_ip" {
  description = "Elastic IP address (if allocated)"
  value       = var.allocate_elastic_ip ? aws_eip.minecraft[0].public_ip : null
}

output "minecraft_server_address" {
  description = "Address to use for connecting to the Minecraft server"
  value       = var.allocate_elastic_ip ? aws_eip.minecraft[0].public_ip : aws_instance.minecraft.public_ip
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.minecraft.id
} 