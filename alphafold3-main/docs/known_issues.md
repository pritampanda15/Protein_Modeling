# Known Issues

## Numerical Accuracy above 5,120 Tokens

AlphaFold 3 does not currently support inference on inputs larger than 5,120
tokens. An error will be raised if the input is larger than this threshold.

This is due to a numerical issue with the custom Pallas kernel implementing the
Gated Linear Unit. The numerical issue only occurs at inputs above the 5,120
tokens threshold, and results in degraded accuracy in the predicted structure.

This numerical issue is unique to the single GPU configuration used in this
repository, and does not affect the results in the
[AlphaFold 3 paper](https://www.nature.com/articles/s41586-024-07487-w).

We hope to resolve this issue soon and remove this check on input size.
