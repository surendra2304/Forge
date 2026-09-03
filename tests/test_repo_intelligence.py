from forge_upgrade.repo_intelligence import RepoIntelligence


def test_repo_map(tmp_path):
    (tmp_path / "a.py").write_text("def x(): pass\n", encoding="utf-8")
    rm = RepoIntelligence(tmp_path).build_map()
    assert rm.files[0].language == "python"
