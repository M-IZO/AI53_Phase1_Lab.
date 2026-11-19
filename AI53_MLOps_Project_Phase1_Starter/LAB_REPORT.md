# Lab Report

#### Marine IZOULET

#### AI53

## Milestone 0

Start with a table of at least six issues. For each one, list the file or setting, explain the problem and suggest a fix.

| # | Issue                                    | File/Setting                                                  | Problem                                                                 | Suggested Fix                                        |
| - | ---------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------- |
| 1 | Only Python's random generator is seeded | `tests/test_reproducibility.py`/ `src/reproducibility.py` | `set_reproducibility` only seeds Python's random generator.           | Add seeding for NumPy and PyTorch random generators. |
| 2 | The  generator has no seed              | `tests/test_reproducibility.py`/ `src/reproducibility.py` | No seed is used in the return                                           | Add seed to the `torch.Generator()`               |
| 3 | DataLoader workers aren't seeded         | `tests/test_reproducibility.py`/ `src/reproducibility.py` | The function body is just `pass`. With `num_workers > 0`            |                                                      |
| 4 | There's no data-quality check            | `src/validate_data.pycrashes or trains on bad data`         |                                                                         |                                                      |
| 5 | No training                              | `src/train.py`                                              | The run starts but logs no params, metrics, dataset, artifacts or model | implement it                                         |
| 6 |                                          |                                                               |                                                                         |                                                      |

## Milestone 1

`pyproject.toml` is a configuration file used in Python projects to specify build system requirements and project metadata. 

`uv.lock` records the exact versions of dependencies installed in the virtual environment, ensuring that the same versions can be installed in other environments for consistency.

`.venv/` is a directory that contains a virtual environment for the project. It isolates the project's dependencies from the global Python environment.

*Does random_state=42 guarantee bit-for-bit identical results on every CPU/GPU/software stack? Explain briefly*

No it does not guarantee bit-for-bit identical results on every CPU/GPU/software stack. 

## Milestone 2 - Extract and track the images

*In one sentence each, state what the Git remote stores, what the DVC remote stores, and whether git push transfers the DVC-managed raw images.*

The Git remote stores the version-controlled files (code, documentation, etc.) while the DVC remote stores the version-controlled data and model files(like images, datasets, etc.). Yes, git push transfers the DVC-managed raw images.