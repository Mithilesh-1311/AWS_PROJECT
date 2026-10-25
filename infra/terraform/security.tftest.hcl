mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = { account_id = "123456789012" }
  }
  mock_data "aws_availability_zones" {
    defaults = { names = ["ap-south-1a"] }
  }
  mock_data "aws_ssm_parameter" {
    defaults = { value = "ami-0123456789abcdef0" }
  }
}

run "secure_single_host_plan" {
  command = plan
  variables {
    access_cidrs   = ["203.0.113.10/32"]
    release_key    = "releases/test.tar.gz"
    release_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.research.block_public_acls && aws_s3_bucket_public_access_block.research.block_public_policy && aws_s3_bucket_public_access_block.research.ignore_public_acls && aws_s3_bucket_public_access_block.research.restrict_public_buckets
    error_message = "Research bucket must block all public access."
  }
  assert {
    condition     = aws_s3_bucket_versioning.research.versioning_configuration[0].status == "Enabled"
    error_message = "Artifact recovery needs bucket versioning."
  }
  assert {
    condition     = aws_instance.host.metadata_options[0].http_tokens == "required" && aws_instance.host.root_block_device[0].encrypted
    error_message = "Require IMDSv2 and encrypted host storage."
  }
  assert {
    condition     = alltrue([for rule in aws_security_group.app.ingress : contains([80, 443], rule.from_port)])
    error_message = "Only proxy ports can be exposed; management uses SSM."
  }
}
