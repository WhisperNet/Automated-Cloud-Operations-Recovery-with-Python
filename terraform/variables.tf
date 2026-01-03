variable vpc_cidr_block{
    description = "cidr block for the vpc"
    type = string
}
variable subnet_cidr_block{
    description = "cidr block for the subnet"
    type = string
}
variable avail_zone{
    description = "availability zone for the subnet"
    type = string
}
variable env_prefix{
    description = "Environet prefix for the infra"
    type = string
}
variable my_ip_cidr{
    description = "CIDR block to acces the ec2 instance using SSH"
    type = string
}
variable ec2_instance_type {
    description = "Instance type of ec2 server"
    type = string
}
variable pubic_key_filepath{
    description = "File path of the public key"
    type = string
}