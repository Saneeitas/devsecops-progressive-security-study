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

  # V09: public policy protection is intentionally disabled for static IaC research.
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

data "aws_iam_policy_document" "public_fixture" {
  statement {
    sid       = "V09PublicRead"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.secure_fixture.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "public_fixture" {
  bucket = aws_s3_bucket.secure_fixture.id
  policy = data.aws_iam_policy_document.public_fixture.json
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secure_fixture" {
  bucket = aws_s3_bucket.secure_fixture.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
