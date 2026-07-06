from phase6.storage import LocalSessionStore


def test_local_session_store_persists_json_and_prunes_oldest(tmp_path):
    store = LocalSessionStore(tmp_path / "phase6.db", max_sessions=2)

    store.create_session("sess_1", tmp_path / "one.jpg")
    store.update_session(
        "sess_1",
        detection_json={"session_id": "sess_1"},
        treatment_json={"recommendations": [{"medicine_name": "demo"}]},
        sync_status="completed",
    )
    store.create_session("sess_2", tmp_path / "two.jpg")
    store.create_session("sess_3", tmp_path / "three.jpg")

    assert store.get_session("sess_1") is None
    assert store.get_session("sess_3")["sync_status"] == "captured"
    assert store.list_sessions()[0]["session_id"] == "sess_3"

