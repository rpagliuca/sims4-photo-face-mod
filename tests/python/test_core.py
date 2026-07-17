from photo_face_mod.core import PhotoAssignmentStore


def test_assign_and_get(tmp_path):
    store = PhotoAssignmentStore(tmp_path)
    store.assign(111, 2)
    assert store.get(111) == 2


def test_get_missing_returns_none(tmp_path):
    store = PhotoAssignmentStore(tmp_path)
    assert store.get(999) is None


def test_assign_overwrites_existing(tmp_path):
    store = PhotoAssignmentStore(tmp_path)
    store.assign(111, 2)
    store.assign(111, 5)
    assert store.get(111) == 5


def test_remove_existing(tmp_path):
    store = PhotoAssignmentStore(tmp_path)
    store.assign(111, 2)
    assert store.remove(111) is True
    assert store.get(111) is None


def test_remove_missing_returns_false(tmp_path):
    store = PhotoAssignmentStore(tmp_path)
    assert store.remove(111) is False


def test_all_returns_every_assignment(tmp_path):
    store = PhotoAssignmentStore(tmp_path)
    store.assign(111, 2)
    store.assign(222, 7)
    assert store.all() == {"111": 2, "222": 7}


def test_persists_across_instances(tmp_path):
    PhotoAssignmentStore(tmp_path).assign(111, 3)
    reopened = PhotoAssignmentStore(tmp_path)
    assert reopened.get(111) == 3


def test_sim_id_accepts_int_or_str_interchangeably(tmp_path):
    store = PhotoAssignmentStore(tmp_path)
    store.assign(111, 4)
    assert store.get("111") == 4


def test_data_dir_created_on_first_write(tmp_path):
    data_dir = tmp_path / "nested" / "mod_data"
    store = PhotoAssignmentStore(data_dir)
    store.assign(111, 1)
    assert data_dir.exists()


def test_no_leftover_tmp_files_after_save(tmp_path):
    store = PhotoAssignmentStore(tmp_path)
    store.assign(111, 1)
    leftovers = list(tmp_path.glob(".tmp_assignments_*"))
    assert leftovers == []
