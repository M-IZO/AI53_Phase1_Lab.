# Lab Report

### Marine IZOULET

### AI53

Start with a table of at least six issues. For each one, list the file or setting, explain the problem and suggest a fix.

| # | Issue                                    | File/Setting                                                  | Problem                                                                 | Suggested Fix                                        |
| - | ---------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------- |
| 1 | Only Python's random generator is seeded | `tests/test_reproducibility.py`/ `src/reproducibility.py` | `set_reproducibility` only seeds Python's random generator.           | Add seeding for NumPy and PyTorch random generators. |
| 2 | The  generator has no seed              | `tests/test_reproducibility.py`/ `src/reproducibility.py` | No seed is used in the return                                           | Add seed to the `torch.Generator()`               |
| 3 | DataLoader workers aren't seeded         | `tests/test_reproducibility.py`/ `src/reproducibility.py` | The function body is just `pass`. With `num_workers > 0`            |                                                      |
| 4 | There's no data-quality check            | `src/validate_data.pycrashes or trains on bad data`         |                                                                         |                                                      |
| 5 | No training                              | `src/train.py`                                              | The run starts but logs no params, metrics, dataset, artifacts or model | implement it                                         |
| 6 |                                          |                                                               |                                                                         |                                                      |
