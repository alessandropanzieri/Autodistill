from ultralytics import YOLO

model = YOLO("./config/yolov8n-seg.pt")
model.train(data = "./config/data.yaml")