resource "aws_s3_bucket" "secure_fixture" {
  bucket = "devsecops-secure-baseline-fixture"
}

resource "aws_s3_bucket_ownership_controls" "secure_fixture" {
  bucket = aws_s3_bucket.secure_fixture.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "secure_fixture" {
  bucket = aws_s3_bucket.secure_fixture.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secure_fixture" {
  bucket = aws_s3_bucket.secure_fixture.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
