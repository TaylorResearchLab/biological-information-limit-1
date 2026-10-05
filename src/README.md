# Scientific implementation

The `bics` package implements the calculations used by the [three examples](../examples/). Each example adds `src/` to the Python search path, so it runs directly from a repository checkout after installing the requirements.

| Module | Calculation |
| --- | --- |
| [tcell.py](bics/tcell.py) | Sequential receptor proofreading and completion metrics |
| [ribosome.py](bics/ribosome.py) | Acceptance information and upstream selection |
| [ribosome_product.py](bics/ribosome_product.py) | Separate product-assay comparison |
| [msn2.py](bics/msn2.py) | Fluorescence processing and binary response comparisons |
| [pairing.py](bics/pairing.py) | Descriptive restoration of reporter pairing |
| [comparison.py](bics/comparison.py) | Primary information and decision calculations |
| [matched_information.py](bics/matched_information.py) | Certified information bounds and independent linear programs |
| [joint_bounds.py](bics/joint_bounds.py) | Exact feasible distributions and classification bounds |
| [information.py](bics/information.py) | Shannon information and numerical enclosures |
| [finite.py](bics/finite.py) | Finite variables and conditional probability laws |

All quantities are evaluated within the explicitly specified model or empirical response definition. Comments describe the assumptions and mathematical qualifications beside the calculations.
