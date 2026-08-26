import asyncio
from unittest.mock import Mock, patch

from textual.containers import VerticalScroll

from configuration_engine.device_summary import DeviceSummary
from configuration_engine.profile import Profile
from configuration_engine.tui import Command, ConfigurationApp


async def _test_refresh_devices_preserves_selected_device() -> None:
    app = ConfigurationApp()

    devices = [
        DeviceSummary(
            friendly_name="Alpha",
            ieee_address="00:11:22:33:44:55:66:01",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
        DeviceSummary(
            friendly_name="Bravo",
            ieee_address="00:11:22:33:44:55:66:02",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
        DeviceSummary(
            friendly_name="Charlie",
            ieee_address="00:11:22:33:44:55:66:03",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
    ]

    refreshed_devices = [
        DeviceSummary(
            friendly_name="Charlie",
            ieee_address="00:11:22:33:44:55:66:03",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
        DeviceSummary(
            friendly_name="Alpha",
            ieee_address="00:11:22:33:44:55:66:01",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
        DeviceSummary(
            friendly_name="Bravo",
            ieee_address="00:11:22:33:44:55:66:02",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
    ]

    async with app.run_test() as pilot:
        device_list = app.query_one("#device-list")

        app.devices = devices

        for number, device in enumerate(
            devices,
            start=1,
        ):
            await device_list.append(
                app.make_device_list_item(
                    number,
                    device,
                )
            )

        device_list.index = 1
        device_list.focus()

        app._load_devices_from_configuration = Mock(
            return_value=refreshed_devices,
        )

        await app.refresh_devices()

        assert [device.friendly_name for device in app.devices] == [
            "Alpha",
            "Bravo",
            "Charlie",
        ]

        assert device_list.index == 1

        assert app.devices[device_list.index].friendly_name == "Bravo"

        await pilot.pause()


def test_refresh_devices_preserves_selected_device() -> None:
    asyncio.run(_test_refresh_devices_preserves_selected_device())


async def _test_refresh_devices_selects_first_device_when_selected_device_disappears() -> None:
    app = ConfigurationApp()

    devices = [
        DeviceSummary(
            friendly_name="Alpha",
            ieee_address="00:11:22:33:44:55:66:01",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
        DeviceSummary(
            friendly_name="Bravo",
            ieee_address="00:11:22:33:44:55:66:02",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
        DeviceSummary(
            friendly_name="Charlie",
            ieee_address="00:11:22:33:44:55:66:03",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
    ]

    refreshed_devices = [
        DeviceSummary(
            friendly_name="Alpha",
            ieee_address="00:11:22:33:44:55:66:01",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
        DeviceSummary(
            friendly_name="Charlie",
            ieee_address="00:11:22:33:44:55:66:03",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
    ]

    async with app.run_test() as pilot:
        device_list = app.query_one("#device-list")

        app.devices = devices

        for number, device in enumerate(
            devices,
            start=1,
        ):
            await device_list.append(
                app.make_device_list_item(
                    number,
                    device,
                )
            )

        device_list.index = 1
        device_list.focus()

        app._load_devices_from_configuration = Mock(
            return_value=refreshed_devices,
        )

        await app.refresh_devices()

        assert [device.friendly_name for device in app.devices] == [
            "Alpha",
            "Charlie",
        ]

        assert device_list.index == 0
        assert app.devices[device_list.index].friendly_name == "Alpha"

        await pilot.pause()


def test_refresh_devices_selects_first_device_when_selected_device_disappears() -> None:
    asyncio.run(
        _test_refresh_devices_selects_first_device_when_selected_device_disappears(),
    )


async def _test_load_devices_clears_devices_when_configuration_load_fails() -> None:
    app = ConfigurationApp()

    app.devices = [
        DeviceSummary(
            friendly_name="Existing",
            ieee_address="00:11:22:33:44:55:66:01",
            manufacturer="Test",
            model_id="test-model",
            firmware="1.0",
        ),
    ]

    async with app.run_test() as pilot:
        app._load_devices_from_configuration = Mock(
            side_effect=OSError("configuration unavailable"),
        )

        app.load_devices()

        assert app.devices == []

        instruction = app.query_one("#instruction")

        assert "Unable to load devices: configuration unavailable" in str(
            instruction.render(),
        )

        await pilot.pause()


def test_load_devices_clears_devices_when_configuration_load_fails() -> None:
    asyncio.run(
        _test_load_devices_clears_devices_when_configuration_load_fails(),
    )


def test_device_status_classes() -> None:
    app = ConfigurationApp()

    assert app.device_status_class("Unknown") == ""

    app.device_status["Test Device"] = "success"

    assert app.device_status_class("Test Device") == "device-success"

    app.device_status["Test Device"] = "unavailable"

    assert app.device_status_class("Test Device") == "device-unavailable"


async def _test_device_status_updates_list_item_class() -> None:
    app = ConfigurationApp()

    device = DeviceSummary(
        friendly_name="Test Device",
        ieee_address="00:11:22:33:44:55:66:01",
        manufacturer="Test",
        model_id="test-model",
        firmware="1.0",
    )

    async with app.run_test() as pilot:
        device_list = app.query_one("#device-list")

        app.devices = [device]

        await device_list.append(
            app.make_device_list_item(
                1,
                device,
            )
        )

        app.mark_device_success("Test Device")

        item = device_list.children[0]

        assert item.has_class("device-success")
        assert not item.has_class("device-unavailable")

        app.mark_device_unavailable("Test Device")

        assert item.has_class("device-unavailable")
        assert not item.has_class("device-success")

        await pilot.pause()


def test_device_status_updates_list_item_class() -> None:
    asyncio.run(
        _test_device_status_updates_list_item_class(),
    )


async def _test_show_help_displays_error_when_help_file_cannot_be_read() -> None:
    app = ConfigurationApp()

    async with app.run_test() as pilot:
        help_view = app.query_one("#help-view")

        assert not help_view.display

        with patch(
            "configuration_engine.tui.files",
        ) as files_mock:
            files_mock.return_value.joinpath.return_value.read_text.side_effect = OSError(
                "help file unavailable"
            )

            app.show_help()

        assert help_view.display

        help_content = app.query_one("#help-content")

        assert "Unable to load help: help file unavailable" in str(
            help_content.render(),
        )

        await pilot.pause()


def test_show_help_displays_error_when_help_file_cannot_be_read() -> None:
    asyncio.run(
        _test_show_help_displays_error_when_help_file_cannot_be_read(),
    )


async def _test_show_help_loads_packaged_help_text() -> None:
    app = ConfigurationApp()

    help_text = "Test help content."

    async with app.run_test() as pilot:
        with patch(
            "configuration_engine.tui.files",
        ) as files_mock:
            files_mock.return_value.joinpath.return_value.read_text.return_value = help_text

            app.show_help()

        help_view = app.query_one("#help-view")
        help_content = app.query_one("#help-content")

        assert help_view.display
        assert str(help_content.render()) == help_text

        await pilot.pause()


def test_show_help_loads_packaged_help_text() -> None:
    asyncio.run(
        _test_show_help_loads_packaged_help_text(),
    )


async def _test_command_list_uses_command_ids() -> None:
    app = ConfigurationApp()

    async with app.run_test() as pilot:
        app._load_devices_from_configuration = Mock(
            return_value=[],
        )

        app.load_devices()

        command_list = app.query_one("#command-list")

        expected_ids = [f"command-{command.name.lower()}" for command in Command]

        actual_ids = [item.id for item in command_list.children]

        assert actual_ids == expected_ids

        await pilot.pause()


def test_command_list_uses_command_ids() -> None:
    asyncio.run(
        _test_command_list_uses_command_ids(),
    )


async def _test_profile_content_scrolls_immediately() -> None:
    app = ConfigurationApp()

    profile = Profile(
        vendor="Test Vendor",
        model="Test Model",
        values={f"property_{index:02d}": index for index in range(30)},
    )

    with patch(
        "configuration_engine.tui.ProfileRepository.read",
        return_value=profile,
    ):
        async with app.run_test() as pilot:
            app.profile_list_profile = "Profile One"

            app.show_profile()

            await pilot.pause()

            profile_content_view = app.query_one(
                "#profile-content-view",
                VerticalScroll,
            )

            assert profile_content_view.has_focus

            initial_scroll_target_y = profile_content_view.scroll_target_y

            profile_content_view.scroll_down(
                animate=False,
                immediate=True,
            )

            assert profile_content_view.scroll_target_y > initial_scroll_target_y


def test_profile_content_scrolls_immediately() -> None:
    asyncio.run(
        _test_profile_content_scrolls_immediately(),
    )
