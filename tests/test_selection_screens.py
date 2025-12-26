"""Tests for cli.screens.selection_screens module."""

import pytest
from textual.app import App
from textual.widgets.selection_list import Selection

from cli.screens.selection_screens import ActionableSelectionList, SingleSelectionList


class TestActionableSelectionList:
    """Tests for ActionableSelectionList widget."""

    def test_submitted_message_stores_selected(self) -> None:
        """Test that Submitted message stores selected items."""
        msg = ActionableSelectionList.Submitted(selected=(1, 2, 3))
        assert msg.selected == (1, 2, 3)

    def test_submitted_message_empty_selection(self) -> None:
        """Test that Submitted message handles empty selection."""
        msg = ActionableSelectionList.Submitted(selected=())
        assert msg.selected == ()

    def test_bindings_configured(self) -> None:
        """Test that expected keybindings are configured."""
        binding_keys = [b.key for b in ActionableSelectionList.BINDINGS]
        assert "a" in binding_keys
        assert "d" in binding_keys

    @pytest.mark.asyncio
    async def test_action_all_selects_all(self) -> None:
        """Test that action_all selects all items."""

        class TestApp(App):
            def compose(self):
                yield ActionableSelectionList(
                    Selection("Item 1", 0),
                    Selection("Item 2", 1),
                    Selection("Item 3", 2),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel_list = app.query_one(ActionableSelectionList)

            # Initially nothing selected
            assert len(sel_list.selected) == 0

            # Select all via action
            sel_list.action_all()
            await pilot.pause()

            assert len(sel_list.selected) == 3

    @pytest.mark.asyncio
    async def test_action_deselect_all_clears_selection(self) -> None:
        """Test that action_deselect_all clears all selections."""

        class TestApp(App):
            def compose(self):
                yield ActionableSelectionList(
                    Selection("Item 1", 0, initial_state=True),
                    Selection("Item 2", 1, initial_state=True),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel_list = app.query_one(ActionableSelectionList)

            # Initially all selected
            assert len(sel_list.selected) == 2

            # Deselect all
            sel_list.action_deselect_all()
            await pilot.pause()

            assert len(sel_list.selected) == 0

    @pytest.mark.asyncio
    async def test_action_submit_posts_message(self) -> None:
        """Test that action_submit posts a Submitted message."""
        messages_received = []

        class TestApp(App):
            def compose(self):
                yield ActionableSelectionList(
                    Selection("Item 1", 0, initial_state=True),
                    Selection("Item 2", 1),
                    Selection("Item 3", 2, initial_state=True),
                )

            def on_actionable_selection_list_submitted(self, event):
                messages_received.append(event.selected)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel_list = app.query_one(ActionableSelectionList)
            sel_list.action_submit()
            await pilot.pause()

        assert len(messages_received) == 1
        assert 0 in messages_received[0]
        assert 2 in messages_received[0]


class TestSingleSelectionList:
    """Tests for SingleSelectionList widget."""

    @pytest.mark.asyncio
    async def test_select_clears_previous_and_selects_new(self) -> None:
        """Test that select() deselects all before selecting new item."""

        class TestApp(App):
            def compose(self):
                yield SingleSelectionList(
                    Selection("Item 1", 0, initial_state=True),
                    Selection("Item 2", 1),
                    Selection("Item 3", 2),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel_list = app.query_one(SingleSelectionList)

            # Initially item 0 is selected
            assert 0 in sel_list.selected
            assert len(sel_list.selected) == 1

            # Select item 1 - should deselect item 0
            sel_list.select(1)
            await pilot.pause()

            assert 1 in sel_list.selected
            assert 0 not in sel_list.selected
            assert len(sel_list.selected) == 1

    @pytest.mark.asyncio
    async def test_toggle_deselects_if_already_selected(self) -> None:
        """Test that toggle() deselects if item is already selected."""

        class TestApp(App):
            def compose(self):
                yield SingleSelectionList(
                    Selection("Item 1", 0, initial_state=True),
                    Selection("Item 2", 1),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel_list = app.query_one(SingleSelectionList)

            # Item 0 is selected
            assert 0 in sel_list.selected

            # Toggle item 0 - should deselect it
            sel_list.toggle(0)
            await pilot.pause()

            assert len(sel_list.selected) == 0

    @pytest.mark.asyncio
    async def test_toggle_selects_if_not_selected(self) -> None:
        """Test that toggle() selects if item is not selected."""

        class TestApp(App):
            def compose(self):
                yield SingleSelectionList(
                    Selection("Item 1", 0),
                    Selection("Item 2", 1),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel_list = app.query_one(SingleSelectionList)

            # Nothing selected initially
            assert len(sel_list.selected) == 0

            # Toggle item 1 - should select it
            sel_list.toggle(1)
            await pilot.pause()

            assert 1 in sel_list.selected
            assert len(sel_list.selected) == 1

    @pytest.mark.asyncio
    async def test_toggle_with_selection_object(self) -> None:
        """Test that toggle() works with Selection objects."""

        class TestApp(App):
            def compose(self):
                yield SingleSelectionList(
                    Selection("Item 1", 0, initial_state=True),
                    Selection("Item 2", 1),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel_list = app.query_one(SingleSelectionList)

            # Toggle using a Selection object
            selection = Selection("Item 2", 1)
            sel_list.toggle(selection)
            await pilot.pause()

            assert 1 in sel_list.selected
            assert 0 not in sel_list.selected

    @pytest.mark.asyncio
    async def test_only_one_item_selected_at_a_time(self) -> None:
        """Test that only one item can be selected at a time."""

        class TestApp(App):
            def compose(self):
                yield SingleSelectionList(
                    Selection("Item 1", 0),
                    Selection("Item 2", 1),
                    Selection("Item 3", 2),
                )

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sel_list = app.query_one(SingleSelectionList)

            # Select multiple items in sequence
            sel_list.select(0)
            await pilot.pause()
            assert 0 in sel_list.selected
            assert len(sel_list.selected) == 1

            sel_list.select(1)
            await pilot.pause()
            assert 1 in sel_list.selected
            assert len(sel_list.selected) == 1

            sel_list.select(2)
            await pilot.pause()
            assert 2 in sel_list.selected
            assert len(sel_list.selected) == 1
