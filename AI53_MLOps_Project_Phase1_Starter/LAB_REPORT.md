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


## Milestone 3 - Implement a Core data-quality gate

uv run --locked pytest -q tests/test_data_validation.py tests/test_validation_contract.py
``` bash
7 passed in 0.06s
``` 

uv run --locked python -m src.validate_data

```json
{
  "classes": [
    "angular_leaf_spot",
    "bean_rust",
    "healthy"
  ],
  "splits": {
    "test": {
      "class_counts": {
        "angular_leaf_spot": 43,
        "bean_rust": 43,
        "healthy": 42
      },
      "images": 128
    },
    "train": {
      "class_counts": {
        "angular_leaf_spot": 345,
        "bean_rust": 348,
        "healthy": 341
      },
      "images": 1034
    },
    "validation": {
      "class_counts": {
        "angular_leaf_spot": 44,
        "bean_rust": 45,
        "healthy": 44
      },
      "images": 133
    }
  },
  "status": "PASS",
  "total_images": 1295
}
```
## Milestone 4 - Design the DVC pipeline from scratch

*Should PREPARE depend on reports/data_quality.json?*

Yes. It is the output of VALIDATE, and this dependency is what puts VALIDATE before PREPARE in the DAG. 

*Should PREPARE also depend directly on data/raw?*

Yes. PREPARE reads the raw images itself. If it only depended on the report, a change to the images that produced an identical report would not be detected, and PREPARE would not run again.

*Which changes in params.yaml should make TRAIN run again?*

Only the keys `src/train.py` and its helpers read: `data.image_size`, `train.batch_size`, `train.epochs`, `train.learning_rate`, `train.dropout`, `train.random_state`, `augmentation.enabled`, `augmentation.horizontal_flip`, `augmentation.rotation_degrees`, `compute.device`, `tracking.uri` and `tracking.experiment`. 

*Why should EVALUATE track selection.run_id?*

EVALUATE does not read `models/model.pt`. It loads the model logged in MLflow for `selection.run_id`. That setting is the only link between EVALUATE and the chosen model. If DVC did not track it, selecting another Run would leave the stage "up to date" and `reports/test_metrics.json` would keep the scores of the old model.

*Which file contains scores that DVC should track as metrics?*

`reports/train_summary.json` (final validation loss, accuracy and macro-F1) for TRAIN, and `reports/test_metrics.json` (test accuracy and macro-F1) for EVALUATE.

uv run --locked dvc stage list

```text
validate  Outputs reports/data_quality.json
prepare   Outputs data/processed/train, data/processed/validation, data/processed/test, d…
train     Outputs models/model.pt, reports/training_curves.png, reports/run_manifest.json…
evaluate  Outputs reports/test_confusion_matrix.png; Reports reports/test_metrics.json
```

uv run --locked dvc dag

```text
        +--------------+          
        | data/raw.dvc |          
        +--------------+          
           **        **           
         **            **         
        *                **       
+----------+               *      
| validate |             **       
+----------+           **         
           **        **           
             **    **             
               *  *               
           +---------+            
           | prepare |            
           +---------+            
           **        **           
         **            **         
        *                *        
  +-------+         +----------+  
  | train |         | evaluate |  
  +-------+         +----------+  
```

EVALUATE does not depend on TRAIN: it depends on the prepared test data and manifests, and gets the model from MLflow through `selection.run_id`.

## Milestone 5 - Record what each MLflow Run used

## Milestone 6 - Predict which stages need to run again

## Milestone 7 - Compare three controlled runs

## Milestone 8 - Select and test one model
