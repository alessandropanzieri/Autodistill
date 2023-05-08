import cv2

image = cv2.imread("qrcode.png")
qrcode = cv2.QRCodeDetector()

retval, decoded_info, points, straight_qrcode = qrcode.detectAndDecodeMulti(image)
image = cv2.polylines(image, points.astype(int), True, (0, 255, 0), 3)

cv2.imwrite("output.jpg", image)