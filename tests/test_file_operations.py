from file_operations import copy_file, copy_folder_contents


def test_copy_file_creates_parent_but_not_filename_directory(tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"map-image")
    target = tmp_path / "exports" / "MT_CMP-1.png"

    result = copy_file(source, target)

    assert result == target
    assert target.is_file()
    assert target.read_bytes() == b"map-image"


def test_copy_folder_contents_preserves_nested_files(tmp_path):
    source = tmp_path / "source"
    (source / "nested").mkdir(parents=True)
    (source / "root.txt").write_text("root", encoding="utf-8")
    (source / "nested" / "child.txt").write_text("child", encoding="utf-8")
    target = tmp_path / "export"

    copy_folder_contents(source, target)

    assert (target / "root.txt").read_text(encoding="utf-8") == "root"
    assert (target / "nested" / "child.txt").read_text(encoding="utf-8") == "child"
