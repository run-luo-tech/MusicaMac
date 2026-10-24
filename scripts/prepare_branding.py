"""Resize supplied artwork and convert icon formats; requires Pillow for regeneration."""
from pathlib import Path
from PIL import Image


def main():
    folder = Path(__file__).resolve().parents[1] / 'assets'
    with Image.open(folder / 'Musica_logo.png') as original:
        image = original.convert('RGBA')
        for size in (80, 256):
            image.resize((size, size), Image.Resampling.LANCZOS).save(folder / f'logo-{size}.png')
        image.resize((256, 256), Image.Resampling.LANCZOS).save(
            folder / 'Musica.ico', sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
        image.resize((1024, 1024), Image.Resampling.LANCZOS).save(folder / 'Musica.icns')


if __name__ == '__main__':
    main()
