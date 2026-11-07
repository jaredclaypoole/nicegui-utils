import math
from collections.abc import Callable
from typing import Any

from nicegui import ui
from nicegui.events import GenericEventArguments


class VirtualScroll(ui.element):
    def __init__(
        self,
        *,
        items: Any,
        render_item: Callable[[int, Any], None],
        item_height: int = 200,
        viewport_height: int = 600,
        overscan: int = 3,
    ) -> None:
        if item_height <= 0:
            raise ValueError("item_height must be positive")
        if viewport_height <= 0:
            raise ValueError("viewport_height must be positive")
        if overscan < 0:
            raise ValueError("overscan must be nonnegative")

        super().__init__("div")

        self.items = items
        self.render_item = render_item
        self.item_height = item_height
        self.overscan = overscan

        # Discovery state.
        self._known_count = 0
        self._exhausted = False
        self._pending_values: dict[int, Any] = {}

        # Mounted NiceGUI element trees.
        self._mounted: dict[int, ui.element] = {}

        self.style(
            f"height: {viewport_height}px;"
            "overflow-y: auto;"
            "overflow-x: hidden;"
        ).classes("w-full")

        with self:
            self._top = ui.element("div")
            self._rows = ui.element("div")
            self._bottom = ui.element("div")

        self.on(
            "scroll",
            self._on_scroll,
            throttle=0.05,
            js_handler=(
                "(e) => emit({"
                "top: e.target.scrollTop,"
                "height: e.target.clientHeight"
                "})"
            ),
        )

        self._update_window(0, viewport_height)

    def _discover_through(self, last_index: int) -> None:
        """Discover items sequentially, stopping at IndexError."""
        while (
            not self._exhausted
            and self._known_count <= last_index
        ):
            index = self._known_count

            try:
                value = self.items[index]
            except IndexError:
                self._exhausted = True
                break

            self._pending_values[index] = value
            self._known_count += 1

    def _on_scroll(self, event: GenericEventArguments) -> None:
        self._update_window(
            float(event.args["top"]),
            float(event.args["height"]),
        )

    def _update_window(
        self,
        scroll_top: float,
        viewport_height: float,
    ) -> None:
        height = self.item_height

        first_visible = max(0, int(scroll_top // height))
        end_visible = math.ceil(
            (scroll_top + viewport_height) / height
        )

        start = max(0, first_visible - self.overscan)
        requested_end = end_visible + self.overscan

        # Discover only as far as the requested window.
        self._discover_through(requested_end - 1)

        end = min(requested_end, self._known_count)
        start = min(start, end)

        wanted = set(range(start, end))
        mounted = set(self._mounted)

        # Delete rows outside the new window.
        for index in mounted - wanted:
            self._mounted.pop(index).delete()

        # Create missing rows without recreating overlap.
        for index in range(start, end):
            if index in self._mounted:
                continue

            value = self._pending_values.pop(
                index,
                None,
            )

            # Previously discovered rows can be
            # retrieved again using __getitem__.
            if value is None:
                value = self.items[index]

            with self._rows:
                row = ui.element("div").style(
                    f"height: {height}px;"
                    "box-sizing: border-box;"
                    "overflow: hidden;"
                ).classes("w-full")

            with row:
                self.render_item(index, value)

            self._mounted[index] = row

            # Insert into the correct position.
            row.move(
                self._rows,
                target_index=index - start,
            )

        # Retain no extra Python-side item values.
        self._pending_values.clear()

        top_height = start * height

        # One extra row of scrollable space allows
        # discovery to continue when length is unknown.
        bottom_count = (
            self._known_count - end
            + int(not self._exhausted)
        )

        self._top.style(
            f"height: {top_height}px",
        )
        self._bottom.style(
            f"height: {bottom_count * height}px",
        )
