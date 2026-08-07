output "public_ip" {
  description = "Fixed Public Elastic IP of the FinOps deployment"
  value       = aws_eip.finops_eip.public_ip
}

output "dashboard_url" {
  description = "URL for React Executive Operations Hub"
  value       = "http://${aws_eip.finops_eip.public_ip}:3000"
}

output "api_url" {
  description = "FastAPI Backend API endpoint"
  value       = "http://${aws_eip.finops_eip.public_ip}:8000"
}
