# Manual Reproduction Suite

Run all 39 source-document scenarios:

```powershell
python -m test_manuals --all
```

Use `--list`, `--smoke`, `--pdf NAME`, `--feature NAME`, or `--milestone M42` to select scenarios.
Reports are written to `test_manuals/outputs/report.html` and `report.md`.

The registry maps every feature-bearing PDF in `datas/` plus the root Overview and Maxwell documents.
`ListOfDocuments.pdf` is an index rather than a feature source and is not counted; the duplicate root copy of
`Predici11_Tutorials.pdf` maps to the same scenario as the `datas/` copy.
