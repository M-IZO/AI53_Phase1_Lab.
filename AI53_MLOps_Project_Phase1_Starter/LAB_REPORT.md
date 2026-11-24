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

uv run --locked pytest -q

```bash
19 passed in 4.62s
```

Git records the exact code and configuration through the commit SHA stored in the Run manifest, together with whether the working tree was dirty.
DVC records which data and outputs the Run used and produced, through the hashes in `dvc.lock` of the raw images, the processed images and manifests.
MLflow records the Run itself, its parameters, per-epoch metrics, training time, the training Dataset input, the report artifacts  and the logged bean-cnn model with its signature, input example and metadata.

## Milestone 6 - Predict which stages need to run again

### 6.1 Predictions

| Change | VALIDATE | PREPARE | TRAIN | EVALUATE |
|---|---|---|---|---|
| Change train.learning_rate | REUSED | REUSED | RERUN | REUSED |
| Change data.image_size | REUSED | RERUN | RERUN | NEEDS UPDATE |
| Edit src/validate_data.py; the quality report stays the same | RERUN | REUSED | REUSED | REUSED |
| Edit only README.md | REUSED | REUSED | REUSED | REUSED |


### 6.3 Decisions before training

 **Main validation metric:** val_macro_f1 at the final epoch. The three classes are almost balanced, but macro-F1 weights every class equally, so a model that ignores one disease is penalized even when accuracy looks fine.
**Tie-break:** if two Runs have the same val_macro_f, pick the one with the lower final val_loss.
**Expected effect of a lower learning rate (0.001 → 0.0003):** smaller weight updates, so with the same 4 epochs the loss should decrease more slowly. I expect higher final train_loss/val_loss and probably a lower val_macro_f1 than Run A, but smoother curves.

### 6.3 / 6.4 Observed results

- **Run A** (baseline, `learning_rate=0.001`): `99bbda976b0c44708038998b08719f38`. Final `val_macro_f1=0.6321`, `val_loss=0.8326`.
- **Run B** (`learning_rate=0.0003`): `9bf7b6dba4f74ddcab6100fe0cb282e5`. Final `val_macro_f1=0.6091`, `val_loss=0.8927`.

| Check | VALIDATE | PREPARE | TRAIN | EVALUATE |
|---|---|---|---|---|
| Baseline `dvc repro train` (Run A) | RERUN | RERUN | RERUN | NOT RUN |
| 1. Run again, nothing changed | REUSED | REUSED | REUSED | NOT RUN |
| 2. Comment added to `src/validate_data.py` | RERUN | REUSED | REUSED | NOT RUN |
| `train.learning_rate` = 0.0003 (Run B) | REUSED | REUSED | RERUN | NOT RUN |

Baseline:
```text
'data/raw.dvc' didn't change, skipping
Running stage 'validate':
> uv run --locked python -m src.validate_data
Generating lock file 'dvc.lock'
Running stage 'prepare':
> uv run --locked python -m src.prepare
Running stage 'train':
> uv run --locked python -m src.train
Training complete. MLflow Run ID: 99bbda976b0c44708038998b08719f38
```

Check 1:
```text
'data/raw.dvc' didn't change, skipping
Stage 'validate' didn't change, skipping
Stage 'prepare' didn't change, skipping
Stage 'train' didn't change, skipping
Data and pipelines are up to date.
```

Check 2 (`reports/data_quality.json` md5 `96529065e4f57b8ad701e3a2fe49c061` before and after):
```text
'data/raw.dvc' didn't change, skipping
Running stage 'validate':
> uv run --locked python -m src.validate_data
Updating lock file 'dvc.lock'
Stage 'prepare' didn't change, skipping
Stage 'train' didn't change, skipping
```

Learning-rate change:
```text
'data/raw.dvc' didn't change, skipping
Stage 'validate' didn't change, skipping
Stage 'prepare' didn't change, skipping
Running stage 'train':
> uv run --locked python -m src.train
Training complete. MLflow Run ID: 9bf7b6dba4f74ddcab6100fe0cb282e5
```

**Comparison with the predictions.** The two rows I could test match the predictions. With the comment in `src/validate_data.py`, VALIDATE reran because one of its deps changed, but it rewrote an identical `reports/data_quality.json`, so PREPARE saw the same hash for that dep and was skipped, and TRAIN with it. Changing `train.learning_rate` reran only TRAIN, the only stage that lists this param. The only extra reruns are in the baseline row: there was no `dvc.lock` yet, so DVC had no stored hashes and had to run VALIDATE, PREPARE and TRAIN once. EVALUATE is NOT RUN in every row because `dvc repro train` only runs TRAIN and its upstream stages, and EVALUATE is on a separate branch.

The lower learning rate behaved as expected: after 4 epochs Run B has a higher val_loss (0.8927 vs 0.8326) and a lower val_macro_f1 (0.6091 vs 0.6321), and its losses were still falling steadily at the last epoch.

## Milestone 7 - Compare three controlled runs

### 7.1 Run C setup and prediction

Run C starts from Run A's settings (`train.learning_rate` back to 0.001) and changes exactly one setting: `augmentation.enabled: true` (random horizontal flip with p=0.5 and random rotation of ±10°, applied to training images only).

**Prediction:** augmentation shows the network a slightly different version of each image every epoch, so the training task is harder. With only 4 epochs and the same seed, I expect a higher `train_loss` than Run A and a validation score close to Run A, possibly slightly lower, because the model does not have enough epochs to benefit from the extra variety. The benefit of augmentation (less overfitting) should mainly appear with longer training. Training time should be about the same, since the flip and rotation are cheap compared with the CNN.

### 7.2 Validation comparison (final epoch = logged model)

All three Runs were checked in MLflow: same seed (42), 4 epochs, batch size 32, dropout 0.3 and the same `training_data_identity` (`8fa943ff…`). Only the controlled setting differs.

| Run | Controlled change | Val. Accuracy | Val. Macro-F1 | Training time | MLflow Run ID |
|---|---|---|---|---|---|
| A | Baseline (lr 0.001, no augmentation) | 0.6466 | 0.6321 | 6.3 s | `99bbda976b0c44708038998b08719f38` |
| B | `train.learning_rate` 0.001 → 0.0003 | 0.6165 | 0.6091 | 6.1 s | `9bf7b6dba4f74ddcab6100fe0cb282e5` |
| C | `augmentation.enabled` false → true | 0.6617 | 0.6487 | 6.2 s | `23e5ed78c9614be5a6c30cc230ac8b18` |

**B vs A.** The prediction is supported: with the smaller learning rate, B learns more slowly. After 4 epochs it has a higher val_loss (0.8927 vs 0.8326), a higher train_loss (0.9198 vs 0.8670) and a lower macro-F1 (−0.023). Its loss curves were still falling at epoch 4, so B is under-trained rather than worse in general: with more epochs it could catch up.

**C vs A.** The prediction is partly supported. As expected, train_loss is higher (0.8770 vs 0.8670) and the training time is unchanged. But the validation scores did not drop: C is slightly better (macro-F1 +0.017, accuracy +0.015) with almost the same val_loss (0.8362 vs 0.8326). The accuracy gap is only 2 of the 133 validation images, so with one seed and a small validation set this difference is too small to say that augmentation is better in general.

By the decision rule from Milestone 6 (highest final val_macro_f1, ties broken by lower val_loss), **Run C** is the best candidate.

*Engineering checkpoint 6.*

**Primary metric.** I use macro-F1 because it computes the F1 score for each of the three classes and averages them with equal weight. Accuracy only counts correct images overall, so two models with similar accuracy can make their errors on different classes, and a model that is weak on one disease can still look good. In plant disease detection, missing one disease completely is a real failure, and macro-F1 exposes it.

**Test set only after choosing.** The test set must give an unbiased estimate of how the chosen model behaves on new images. If I compared A, B and C on the test set and kept the best, the test set would become part of model selection, and the reported score would be optimistically biased. So I choose with the validation set only, then evaluate that single model once on the test set in Milestone 8.

## Milestone 8 - Select and test one model

### Selection

- **Selected Run:** C (augmentation on), Run ID `23e5ed78c9614be5a6c30cc230ac8b18`.
- **Main metric:** final-epoch val_macro_f1 = **0.6487**, the highest of the three Runs (A: 0.6321, B: 0.6091). No tie, so the val_loss tie-break was not needed.
- **Other evidence:** C also has the highest validation accuracy (0.6617). Its val_loss (0.8362) is almost the same as A's (0.8326), and its training time is the same (6.2 s). In MLflow, C used the same seed, epochs, batch size, dropout and training_data_identity as A, so the only difference is augmentation.
- **Trade-off / limitation:** C beats A by only 0.017 macro-F1, about 2 of the 133 validation images, with a single seed. Another seed could reverse the ranking, so this choice is weak evidence that augmentation helps in general. All Runs were also trained for only 4 epochs and their losses were still falling, so none of them is fully trained; C's slightly higher val_loss than A also shows the gain is not clear-cut.

`selection.run_id` in params.yaml is set to `23e5ed78c9614be5a6c30cc230ac8b18`. The other settings are left as they are.

### Final test results

uv run --locked dvc repro evaluate

```text
'data/raw.dvc' didn't change, skipping
Stage 'validate' didn't change, skipping
Stage 'prepare' didn't change, skipping
Running stage 'evaluate':
> uv run --locked python -m src.evaluate
Loading selected model: runs:/23e5ed78c9614be5a6c30cc230ac8b18/bean-cnn
```

EVALUATE accepted the Run: it is FINISHED, in the bean-image-classification experiment, with matching image_size (96), class order and training_data_identity (`8fa943ff…`).

reports/test_metrics.json

```json
{
  "selected_run_id": "23e5ed78c9614be5a6c30cc230ac8b18",
  "test_accuracy": 0.640625,
  "test_macro_f1": 0.6366339869281047,
  "training_data_identity": "8fa943ff6c17a3c874d2b152e9d7980602a5cd50c0d8156625bd00590a3d8c6c"
}
```

| Selected Run | Test accuracy | Test macro-F1 | Val. macro-F1 |
|---|---|---|---|
| C `23e5ed78c9614be5a6c30cc230ac8b18` | 0.6406 (82/128) | 0.6366 | 0.6487 |

The test macro-F1 (0.637) is close to the validation macro-F1 (0.649), so the validation score was a fair estimate and the selection did not overfit the validation set much.

reports/test_confusion_matrix.png (rows = true class):

| True \ Predicted | angular_leaf_spot | bean_rust | healthy | Recall |
|---|---|---|---|---|
| angular_leaf_spot | 23 | 11 | 9 | 0.53 |
| bean_rust | 7 | 25 | 11 | 0.58 |
| healthy | 2 | 6 | 34 | 0.81 |

The model recognizes healthy leaves well (recall 0.81) but confuses the two diseases with each other and with healthy leaves. The most serious error for a farmer is that 20 of the 86 diseased leaves (9 + 11) are predicted healthy, so the disease would be missed. With 4 epochs this model is a working pipeline baseline, not a model ready for use.
