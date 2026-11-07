from pathlib import Path
from urllib.request import urlopen

from nicegui import app


class Images:
    def __init__(
        self,
        *,
        count: int = 10_000,
        directory: Path = Path(".image_cache"),
        width: int = 600,
        height: int = 400,
    ) -> None:
        self.count = count
        self.directory = directory.resolve()
        self.width = width
        self.height = height

        self.directory.mkdir(parents=True, exist_ok=True)
        app.add_static_files("/images", self.directory)

    def __getitem__(self, index: int) -> str:
        if not 0 <= index < self.count:
            raise IndexError(index)

        filename = f"image_{index:06d}.jpg"
        path = self.directory / filename

        if not path.exists():
            url = (
                f"https://picsum.photos/seed/{index}/"
                f"{self.width}/{self.height}.jpg"
            )

            with urlopen(url, timeout=15) as response:
                data = response.read()

            # Write atomically to avoid partial cached files.
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(path)

            print(f"Downloaded image {index}")

        return f"/images/{filename}"
