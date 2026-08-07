variable "aws_region" {
  type        = string
  description = "AWS deployment region"
  default     = "us-east-1"
}

variable "instance_type" {
  type        = string
  description = "EC2 compute instance type"
  default     = "t3.large"
}

variable "app_name" {
  type        = string
  description = "Application stack identifier"
  default     = "finops-agent"
}

variable "gemini_api_key" {
  type        = string
  description = "Google AI Studio Gemini API Key"
  default     = ""
  sensitive   = true
}

variable "telegram_bot_token" {
  type        = string
  description = "Telegram Bot Token from @BotFather"
  default     = ""
  sensitive   = true
}
