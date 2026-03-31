from google.cloud import vision


def extract_text_from_image(image_bytes: bytes) -> str:

    client = vision.ImageAnnotatorClient()

    image = vision.Image(content=image_bytes)

    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    texts = response.text_annotations

    if not texts:
        return ""

    return texts[0].description