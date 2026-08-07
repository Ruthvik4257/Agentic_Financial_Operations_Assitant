data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical Ubuntu
}

resource "aws_instance" "finops_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.finops_subnet.id
  vpc_security_group_ids      = [aws_security_group.finops_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size           = 40
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = templatefile("${path.module}/userdata.sh", {
    GEMINI_API_KEY     = var.gemini_api_key
    TELEGRAM_BOT_TOKEN = var.telegram_bot_token
  })

  tags = {
    Name = "${var.app_name}-server"
  }
}

resource "aws_eip" "finops_eip" {
  instance = aws_instance.finops_server.id
  domain   = "vpc"

  tags = {
    Name = "${var.app_name}-eip"
  }
}
