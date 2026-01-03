output public-ip-1 {
  value       = aws_instance.nginx-server.public_ip
}

output public-ip-2 {
  value       = aws_instance.nginx-server-2.public_ip
}