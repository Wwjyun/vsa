# VSA data format 2.0

VSA 0.4.x reads the version 2.0 directory and CSV contract described here. Data remains outside the application repository and is selected with `VSA_DATA_ROOT`.

Version 2.0 differs from 1.0 in stage identity only: the process stages are named `STAGE1`-`STAGE8`, and the six adjacent-stage comparisons stay `LOSS1`-`LOSS6`. Directory layout and the CSV contract are unchanged, so a 1.0 data root is read by 2.0 once its stage folders are renamed.

## Stage vocabulary

`config.STAGE_SEQUENCE` is the only source of stage names:

```text
STAGE1  LOSS1  STAGE2  LOSS2  STAGE3  LOSS3  STAGE4  LOSS4  STAGE5  LOSS5  STAGE6  LOSS6  STAGE7  STAGE8
```

`LOSS<n>` is not a stage of its own: it compares the two stages named in `config.LOSS_STAGE_PAIRS`, so `LOSS1` compares `STAGE1` with `STAGE2`.

## Directory contract

```text
<root>/<product>/csv/<lot>/<stage>/<component>.csv
<root>/<product>/map/<lot>/<stage>/<component>.<image extension>
<root>/<product>/roi/<lot>/<stage>/<component>/<package-no>.tiff
<root>/<product>/org/<lot>/<stage>/<component>/...
<root>/<product>/bar/<lot>/<stage>/<stage>.png
<root>/<product>/example/<stage>/ok.tiff
```

Product, lot, stage, component, and package values are single path components. Separators, traversal values, control characters, and Windows-reserved names are rejected.

## CSV contract

UTF-8 CSV files require exactly these semantic fields (additional fields are allowed):

| Field | Contract |
| --- | --- |
| `No` | Non-null ROI/package identifier |
| `Row` | Non-null numeric row coordinate |
| `Col` | Non-null numeric column coordinate |
| `DefectType` | Defect classification label |

Loss-map stages require unique `(Row, Col)` coordinates. Duplicate coordinates are rejected instead of producing a many-to-many merge. The interactive loss map uses an inner join; analysis code can explicitly request `inner`, `outer`, `left`, or `right`.

## Compatibility policy

- Backward-compatible additions may add optional columns or image extensions.
- Renaming a required field, changing coordinate meaning, or changing stage identity requires a new major data-format version.
- Unsupported or malformed data must fail with a visible validation message; it must not silently generate a map.
