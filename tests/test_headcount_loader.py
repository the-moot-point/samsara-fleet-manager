import headcount_loader


def test_load_headcount_data():
    mapping = headcount_loader.load_headcount_data("Headcount Report.xlsx")
    # Known first row values from the sample file
    info = mapping.get("613")
    assert info
    assert info["name"] == "SAMUEL ABASCAL"
    assert info["email"] == "sabascal@chaparraldist.com"
    assert info["phone"].startswith("151266")
    assert info["location_tag_id"] == "2762148"
