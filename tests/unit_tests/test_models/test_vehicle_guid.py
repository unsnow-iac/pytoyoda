"""Regression tests for the vehicle guid response model."""

from pytoyoda.models.endpoints.vehicle_guid import VehiclesResponseModel


def _response(payload: list[dict]) -> dict:
    return {
        "status": {"messages": [{"responseCode": "ONE-VL-10000"}]},
        "payload": payload,
    }


def test_vehicle_without_remote_display_still_parses():  # noqa: D103
    # Toyota stopped sending remoteDisplay (now optional, like most fields).
    # A single omitted field must not collapse the whole payload to None,
    # which previously made the account look like it had no vehicles.
    model = VehiclesResponseModel.model_validate(
        _response([{"vin": "SB1ZB3AE50E022886", "modelName": "Corolla"}])
    )
    assert model.payload is not None
    assert len(model.payload) == 1
    assert model.payload[0].vin == "SB1ZB3AE50E022886"
    assert model.payload[0].car_model_name == "Corolla"
    assert model.payload[0].remote_display is None
