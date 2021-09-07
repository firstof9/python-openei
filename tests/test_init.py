"""Test main functions."""
from freezegun import freeze_time
import pytest
import openeihttp


def test_get_lookup_data(test_lookup, lookup_mock):
    """Test v4 Status reply"""
    status = test_lookup.lookup_plans()
    assert status == {
        "Arizona Public Service Co": [
            {"name": "Time Advantage 7pm to noon", "label": "539fba68ec4f024bc1dc2db3"},
            {
                "name": "Residential Bundled & Adjustments No Tax TOU; Time Adv Super peak 7PM-Noon (ET-SP)",
                "label": "542aec8a5257a310694b1ab6",
            },
            {
                "name": "Residential Service Bundled Standard rate",
                "label": "55563ddf5457a3bf6c8b4570",
            },
            {
                "name": "Residential Bundled & Adjustments No Tax TOU ; Time Adv 7PM-Noon  (ET-2)",
                "label": "55563df55457a35e758b4568",
            },
            {
                "name": "Residential Bundled & Adjustments No Tax TOU w/ Demand; Combined Adv  7PM-Noon (ECT-2)",
                "label": "562bea025457a31838418740",
            },
            {
                "name": "Residential Service Bundled Standard rate",
                "label": "5743aa135457a3a636906f5b",
            },
            {
                "name": "Residential Service TOU Time Advantage 7PM-Noon (ET-2)",
                "label": "574613aa5457a3557e906f5b",
            },
            {
                "name": "Residential Service TOU Combined Advantage 7PM-Noon  (ECT-2)",
                "label": "574615f85457a3557e906f5c",
            },
            {
                "name": "Residential Service Standard (E-12)",
                "label": "5748ab725457a37e7d906f5b",
            },
            {
                "name": "Residential Service TOU Time Advantage 7PM-Noon (ET-2)",
                "label": "5748ac7a5457a37d7d906f5b",
            },
            {
                "name": "Residential Service Standard (E-12)",
                "label": "5881345e5457a35973316ce7",
            },
            {
                "name": "Residential Service TOU Time Advantage 7PM-Noon (ET-2)",
                "label": "588135ee5457a3873f316ce6",
            },
            {
                "name": "Residential Service TOU Combined Advantage 7PM-Noon  (ECT-2)",
                "label": "5890c92f5457a36c373dbec0",
            },
            {
                "name": "Residential Service Standard (E-12) Low Income",
                "label": "59fcde8e5457a3a04cc05084",
            },
            {
                "name": "Residential Service Standard (E-12) [Frozen]",
                "label": "5a592dee5457a3931d423a81",
            },
            {
                "name": "Residential Service TOU Time Advantage 7PM-Noon (ET-2) [Frozen]",
                "label": "5a5930055457a36274423a7d",
            },
            {
                "name": "Residential Service TOU Combined Advantage 7PM-Noon  (ECT-2) [Frozen]",
                "label": "5a5930bf5457a3371c423a7e",
            },
            {
                "name": "Residential Time of Use (Saver Choice)",
                "label": "5a5933d25457a3ad69423a81",
            },
            {
                "name": "Residential Service (Saver Choice Plus)",
                "label": "5a5935475457a3ad69423a82",
            },
            {
                "name": "Residential Service (Saver Choice Max)",
                "label": "5a5936ef5457a36274423a7f",
            },
            {
                "name": "Extra Small Residential Service (Lite Choice)",
                "label": "5a5937bb5457a3b71c423a7f",
            },
            {
                "name": "Small Residential Service (Premier Choice)",
                "label": "5a59388c5457a3931d423a84",
            },
            {
                "name": "Large Residential Service (Premier Choice Large)",
                "label": "5a5939515457a3371c423a7f",
            },
            {
                "name": "Residential Service (Pilot Technology Rate)",
                "label": "5a593d815457a3371c423a80",
            },
            {
                "name": "Extra Small Residential Service (Lite Choice) R-XS",
                "label": "5cacc5605457a379257780e2",
            },
            {
                "name": "Small Residential Service (Premier Choice) R-Basic",
                "label": "5cacc6545457a3634c7780e2",
            },
            {
                "name": "Large Residential Service (Premier Choice Large) R-Basic L [Frozen]",
                "label": "5cacc6e75457a3a8497780e2",
            },
            {
                "name": "Residential Time of Use (Saver Choice) TOU-E",
                "label": "5cacc7715457a393487780e2",
            },
            {
                "name": "Residential Service (Saver Choice Max)",
                "label": "5cacc9ae5457a3c6517780e2",
            },
            {
                "name": "Residential Service (Saver Choice Plus) R-2",
                "label": "5cacc9d15457a31d537780e2",
            },
            {
                "name": "Residential Service (Saver Choice Max) R-3",
                "label": "5caccb2f5457a3c8517780e2",
            },
            {
                "name": "Residential Service (Pilot Technology Rate) R-Tech",
                "label": "5caccd925457a31a537780e2",
            },
        ]
    }


@freeze_time("2021-08-13 10:21:34")
def test_get_rate_data(test_rates, plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.current_rate
    assert status == 0.06118


@freeze_time("2021-08-13 13:20:00")
def test_get_rate_data_2(test_rates, plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.current_rate
    assert status == 0.24477


@freeze_time("2021-08-14 13:20:00")
def test_get_rate_data_weekend(test_rates, plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.current_rate
    assert status == 0.06118


@freeze_time("2021-08-14 13:20:00")
def test_get_rate_data_weekend_demand(test_rates, demand_plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.current_demand_rate
    assert status == 0


@freeze_time("2021-08-13 10:21:34")
def test_get_rate_data_demand(test_rates, demand_plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.current_demand_rate
    assert status == 0


@freeze_time("2021-08-13 17:20:00")
def test_get_rate_data_2_demand(test_rates, demand_plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.current_demand_rate
    assert status == 8.4


def test_get_demand_unit(test_rates, demand_plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.demand_unit
    assert status == "kW"


def test_get_distributed_generation(test_rates, plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.distributed_generation
    assert status == "Net Metering"


def test_get_aproval(test_rates, plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.approval
    assert status


def test_get_name(test_rates, plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.rate_name
    assert status == "Residential Service TOU Time Advantage 7PM-Noon (ET-2)"


def test_get_lookup_data_404(test_lookup, lookup_mock_404):
    """Test lookup error 404"""
    with pytest.raises(openeihttp.UrlNotFound):
        test_lookup.lookup_plans()


def test_get_lookup_data_401(test_lookup, lookup_mock_401):
    """Test lookup error 401"""
    with pytest.raises(openeihttp.NotAuthorized):
        test_lookup.lookup_plans()


def test_get_plan_data_404(test_rates, plandata_mock_404):
    """Test rate schedules."""
    with pytest.raises(openeihttp.UrlNotFound):
        test_rates.update()


def test_get_plan_data_401(test_rates, plandata_mock_401):
    """Test rate schedules."""
    with pytest.raises(openeihttp.NotAuthorized):
        test_rates.update()


def test_get_plan_data_api_err(test_rates, plandata_mock_api_err, caplog):
    """Test rate schedules."""
    with pytest.raises(openeihttp.APIError):
        test_rates.update()
        assert (
            "No api_key was supplied. Get one at https://api.openei.org:443"
            in caplog.text
        )


def test_get_lookup_data_api_err(test_lookup, lookup_mock_api_err, caplog):
    """Test rate schedules."""
    with pytest.raises(openeihttp.APIError):
        test_lookup.lookup_plans()
        assert (
            "No api_key was supplied. Get one at https://api.openei.org:443"
            in caplog.text
        )


def test_get_all_rates(test_rates, plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.all_rates
    assert status == [0.24477, 0.06118, 0.19847, 0.06116]


def test_get_all_rates_demand(test_rates, demand_plandata_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.all_rates
    assert status == [0.07798, 0.11017, 0.1316]


@freeze_time("2021-08-13 10:21:34")
def test_get_rate_data(test_rates, plandata_radius_mock):
    """Test rate schedules."""
    test_rates.update()
    status = test_rates.current_rate
    assert status == 0.06118
