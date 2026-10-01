data "aws_iam_policy_document" "product_reader" {
  statement {
    sid    = "V11WildcardAdministration"
    effect = "Allow"
    # V11: intentionally excessive wildcard permissions for static IaC research.
    actions   = ["*"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "product_reader" {
  name        = "devsecops-secure-baseline-product-reader"
  description = "V11 experimental wildcard policy; never deploy"
  policy      = data.aws_iam_policy_document.product_reader.json
}
