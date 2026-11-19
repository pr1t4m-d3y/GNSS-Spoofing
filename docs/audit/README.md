# Audit scripts and logs

These scripts produced the numbers in [../AUDIT.md](../AUDIT.md). They ran against the repository as it was at commit `b4e6aa0`, before the restructure: they expect the working directory `GNSS_Security_Package/`, a `backend/utils.py` module and `train.xls` next to it. None of that exists any more, so they are kept as a record, not as runnable tooling. The maintained equivalent is `make eval` (see [../../evals/run.py](../../evals/run.py)).

Logs are in `output/`. They were produced with Python 3.14.8, scikit-learn 1.9.1, pandas 3.1.1 and numpy 2.5.5, loading a model pickled with scikit-learn 1.6.1.
