from rembg import remove
from pathlib import Path
from cv2 import imread, threshold, findContours, RETR_CCOMP, THRESH_BINARY, CHAIN_APPROX_NONE

for image in Path(".").glob("./datasets/images/*.*"):

    input = imread(str(image))
    alpha = remove(input)[:, :, 3]

    mask = threshold(alpha, 0, 255, THRESH_BINARY)[1]
    contours = findContours(mask, RETR_CCOMP, CHAIN_APPROX_NONE)[0]

    segmentation = []
    for item in contours:
        contour = item.flatten().tolist()
        contour = [(contour[j], contour[j + 1]) for j in range(0, len(contour), 2)]
        contour = [(x / input.shape[1], y / input.shape[0]) for x, y in contour]
        segmentation += contour

    with open(f"./datasets/labels/{image.stem}.txt", "w") as annotations:
        annotations.write(f"0 {' '.join([f'{x:.2f} {y:.2f}' for x, y in segmentation])}")