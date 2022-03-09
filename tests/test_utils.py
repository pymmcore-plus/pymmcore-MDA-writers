from pathlib import Path

from pymmcore_mda_writers import BaseWriter


def test_unique_folder(tmp_path: Path):
    base_folder = tmp_path / "data/run"
    unique = BaseWriter.get_unique_folder
    for i in range(3):
        print("here: ", i)
        print(unique(base_folder, create=True))
    unique(base_folder)

    data_folders = list(map(str, set(tmp_path.glob("data/run_*"))))
    print(data_folders)
    expected = [
        "run_1",
        "run_2",
        "run_3",
    ]
    for e in expected:
        assert str(tmp_path / "data" / e) in data_folders
