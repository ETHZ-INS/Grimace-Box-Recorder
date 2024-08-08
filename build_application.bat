call conda activate GrimaceRecorder
pyinstaller^
 --add-data "C:\Users\Me\anaconda3\envs\GrimaceRecorder\Lib\site-packages\ultralytics\cfg\default.yaml;./ultralytics/cfg"^
 --add-data "models/frame_quality.pt;./models"^
 --add-data "models/face_cropper.pt;./models"^
 --add-data "models/grimace_scorer.pt;./models"^
 --add-data "camera_config/top.pfs;./camera_config"^
 --add-data "camera_config/front.pfs;./camera_config"^
 --onedir^
 --noconsole^
 --name "Grimace Box"^
 --icon "res/grimace_box_icon.ico"^
 main.py -y