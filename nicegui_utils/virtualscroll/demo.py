from nicegui import ui

from .virtualscroll import VirtualScroll
from .images import Images


def demo() -> None:
    def render_image(index: int, path: str) -> None:
        with ui.row().classes("w-full h-full items-center no-wrap"):
            ui.image(path).classes("h-full w-48").props(
                "fit=contain"
            )

            with ui.column():
                ui.label(f"Image {index:,}")
                ui.input("Notes")
                ui.button(
                    "Inspect",
                    on_click=lambda: ui.notify(path),
                )


    @ui.page("/")
    def page():
        VirtualScroll(
            items=Images(),
            render_item=render_image,
            item_height=180,
            viewport_height=600,
            overscan=5,
        )

def run(reload=False, **kwargs):
    demo()
    ui.run(reload=reload, **kwargs)


if __name__ in {"__main__", "__mp_main__"}:
    run()