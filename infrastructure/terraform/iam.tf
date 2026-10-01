data "aws_iam_policy_document" "product_reader" {
  statement {
    sid       = "ReadFixtureObjects"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.secure_fixture.arn}/products/*"]
  }
}

resource "aws_iam_policy" "product_reader" {
  name        = "devsecops-secure-baseline-product-reader"
  description = "Least-privilege read access to fixture product objects"
  policy      = data.aws_iam_policy_document.product_reader.json
}
