output "instance_id" {
  description = "ID of the EC2 instance"
  value       = module.minecraft_server.instance_id
}

output "minecraft_server_address" {
  description = "Address to use for connecting to the Minecraft server"
  value       = module.minecraft_server.minecraft_server_address
}

output "connection_instructions" {
  description = "Instructions for connecting to the Minecraft server"
  value       = <<-EOT
    Minecraft Server Address: ${module.minecraft_server.minecraft_server_address}
    
    To connect to the server:
    1. Open Minecraft
    2. Click on "Multiplayer"
    3. Click "Add Server"
    4. Enter a name for the server (e.g. "My Minecraft Server")
    5. Enter the server address: ${module.minecraft_server.minecraft_server_address}
    6. Click "Done" and then select your server to join
    
    To SSH into the server:
    ssh -i <your-private-key-path> ubuntu@${module.minecraft_server.minecraft_server_address}
  EOT
} 