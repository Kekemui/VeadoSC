from base64 import b64decode
from io import BytesIO
from PIL import Image, ImageFile


def get_image_from_b64(b64: str) -> ImageFile.ImageFile:
    image_bytes = b64decode(b64)
    return Image.open(BytesIO(image_bytes))


def get_image_from_path(path: str) -> ImageFile.ImageFile:
    return Image.open(path)
