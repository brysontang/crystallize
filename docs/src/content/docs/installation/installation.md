---
title: Installation Instructions
description: Installation instructions for the Crystallize framework.
---

Clearly and explicitly introduce users to how they install Crystallize, explicitly focusing on straightforward steps. Explicitly state that Crystallize is easily available from PyPI, explicitly providing the explicit, minimal command clearly for installation:

bash

CopyEdit

`pip install crystallize-ml`

Explicitly outline basic compatibility explicitly (Python version, dependencies explicitly). Explicitly mention that Crystallize has minimal core dependencies explicitly (numpy, scipy, pandas clearly), keeping installations explicit and clean.

Explicitly and clearly emphasize explicit best practices explicitly: using a clean virtual environment explicitly. Explicitly provide clear, concise instructions explicitly for popular virtual environment tools clearly:

- **Pixi** (modern, popular clearly in data science):

bash

CopyEdit

`pixi init pixi add crystallize-ml`

- **Conda** (explicitly common clearly in scientific workflows):

bash

CopyEdit

`conda create -n crystallize python=3.11 conda activate crystallize pip install crystallize-ml`

Explicitly provide users explicit confidence explicitly through simple verification instructions clearly:

bash

CopyEdit

`python -c "import crystallize; print(crystallize.__version__)"`
