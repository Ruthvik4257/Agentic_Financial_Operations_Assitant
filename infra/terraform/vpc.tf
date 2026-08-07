resource "aws_vpc" "finops_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.app_name}-vpc"
  }
}

resource "aws_subnet" "finops_subnet" {
  vpc_id                  = aws_vpc.finops_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "${var.app_name}-public-subnet"
  }
}

resource "aws_internet_gateway" "finops_gw" {
  vpc_id = aws_vpc.finops_vpc.id

  tags = {
    Name = "${var.app_name}-igw"
  }
}

resource "aws_route_table" "finops_rt" {
  vpc_id = aws_vpc.finops_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.finops_gw.id
  }

  tags = {
    Name = "${var.app_name}-route-table"
  }
}

resource "aws_route_table_association" "finops_rta" {
  subnet_id      = aws_subnet.finops_subnet.id
  route_table_id = aws_route_table.finops_rt.id
}
