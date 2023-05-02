from ultralytics import YOLO

model = YOLO("./config/model.pt")
results = model("./test.jpg")
'''
for result in results:
    boxes = result.boxes
    masks = result.mask
    probs = result.probs

print(boxes, masks, probs)
'''
print(results)