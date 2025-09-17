# AWS EKS module (skeleton)
# Creates an EKS cluster with a single managed node group.
# Operators must supply proper IAM roles and refine sizing, networking, and security for production.

variable "cluster_name" {
  type    = string
  default = "data-mcp-eks"
}

variable "region" {
  type    = string
  default = "us-west-2"
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "node_group_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "desired_capacity" {
  type    = number
  default = 1
}

provider "aws" {
  region = var.region
}

# IAM role and policies for EKS (placeholder)
resource "aws_iam_role" "eks_cluster" {
  name = "${var.cluster_name}-cluster-role"
  assume_role_policy = data.aws_iam_policy_document.eks_cluster_assume_role.json
  tags = { Name = "${var.cluster_name}-cluster-role" }
}

data "aws_iam_policy_document" "eks_cluster_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids = concat(var.public_subnet_ids, var.private_subnet_ids)
  }

  depends_on = []
}

# Managed node group IAM role (placeholder)
resource "aws_iam_role" "node_group" {
  name = "${var.cluster_name}-nodegroup-role"
  assume_role_policy = data.aws_iam_policy_document.node_assume_role.json
}

data "aws_iam_policy_document" "node_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_eks_node_group" "default" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${var.cluster_name}-ng"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids

  scaling_config {
    desired_size = var.desired_capacity
    max_size     = max(var.desired_capacity, 2)
    min_size     = 1
  }

  instance_types = var.node_group_instance_types
}

output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  value = aws_eks_cluster.this.certificate_authority[0].data
}
