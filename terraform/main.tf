provider "aws" {
    region = "us-east-1"
}

resource "aws_vpc" "nginx-app-vpc" {
    cidr_block = var.vpc_cidr_block
    tags = {
        Name = "${var.env_prefix}-vpc"
    }
}
# variable vpc_id  {}
# variable subnet_cidr_block {}
# variable avail_zone {}
# variable env_prefix {}
# variable default_route_table_id {}

# module nginx-app-subnet-1 {
#   source = "./modules/subnet"
#   vpc_id = aws_vpc.nginx-app-vpc.id
#   subnet_cidr_block = var.subnet_cidr_block
#   avail_zone = var.avail_zone
#   env_prefix = var.env_prefix
#   default_route_table_id = aws_vpc.nginx-app-vpc.default_route_table_id
# }

resource "aws_subnet" "nginx-subnet-1" {
    vpc_id = aws_vpc.nginx-app-vpc.id
    cidr_block= var.subnet_cidr_block
    availability_zone = var.avail_zone
    tags = {
        Name = "${var.env_prefix}-subnet-1"
    }
}


resource "aws_internet_gateway" "nginx-gw" {
  vpc_id = aws_vpc.nginx-app-vpc.id

  tags = {
    Name = "${var.env_prefix}-gw"
  }
}

resource "aws_default_route_table" "nginx-default-route-table" {
    default_route_table_id = aws_vpc.nginx-app-vpc.default_route_table_id

    route {
        cidr_block= "0.0.0.0/0"
        gateway_id= aws_internet_gateway.nginx-gw.id
    }

    tags = {
        Name = "${var.env_prefix}-route-table"
    }
}

# variable vpc_id {}
# variable env_prefix {}
# variable my_ip_cidr {}
# variable pubic_key_filepath {}
# variable ec2_instance_type {}
# variable subnet_id {}output public-ip-1 {
#   value       = aws_instance.nginx-server.public_ip
# }
# variable avail_zone {}

# module nginx-webserver {
#     source = "./modules/webserver"
#     vpc_id = aws_vpc.nginx-app-vpc.id
#     env_prefix = var.env_prefix
#     my_ip_cidr = var.my_ip_cidr
#     pubic_key_filepath = var.pubic_key_filepath
#     ec2_instance_type = var.ec2_instance_type
#     subnet_id= aws_subnet.nginx-subnet-1.id
#     avail_zone= var.avail_zone
# }

resource "aws_default_security_group" "nginx-sg" {
  vpc_id      = aws_vpc.nginx-app-vpc.id

  tags = {
    Name = "${var.env_prefix}-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "allow-8080" {
  security_group_id = aws_default_security_group.nginx-sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8080
  ip_protocol       = "tcp"
  to_port           = 8080
}

resource "aws_vpc_security_group_ingress_rule" "allow-ssh" {
  security_group_id = aws_default_security_group.nginx-sg.id
  cidr_ipv4         = var.my_ip_cidr
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "allow-all-inbound" {
  security_group_id = aws_default_security_group.nginx-sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_key_pair" "deployer" {
  key_name   = "deployer-key"
  public_key = file(var.pubic_key_filepath)
}


data "aws_ami" "aws-linux" {
  most_recent = true

  filter {
    name   = "name"
    values = ["al2023-ami-2023.9.20251110.1-kernel-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["137112412989"] # Amazon
}

resource "aws_instance" "nginx-server" {
  ami           = data.aws_ami.aws-linux.id
  instance_type = var.ec2_instance_type
  subnet_id = aws_subnet.nginx-subnet-1.id
  availability_zone = var.avail_zone
  vpc_security_group_ids = [aws_default_security_group.nginx-sg.id]
  key_name = aws_key_pair.deployer.key_name
  associate_public_ip_address = true
  user_data= file("start-up.sh")
  user_data_replace_on_change = true
  tags = {
    Name = "${var.env_prefix}-nginx-server",
    env = "prod"
  }
}

resource "aws_instance" "nginx-server-2" {
  ami           = data.aws_ami.aws-linux.id
  instance_type = var.ec2_instance_type
  subnet_id = aws_subnet.nginx-subnet-1.id
  availability_zone = var.avail_zone
  vpc_security_group_ids = [aws_default_security_group.nginx-sg.id]
  key_name = aws_key_pair.deployer.key_name
  associate_public_ip_address = true
  user_data= file("start-up.sh")
  user_data_replace_on_change = true
  tags = {
    Name = "${var.env_prefix}-nginx-server-2",
    env = "prod"
  }
}




