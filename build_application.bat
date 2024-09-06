:: The pyinstaller command is provided by the pyinstaller Python module, so the command needs to be executed inside the conda environment
call conda activate GrimaceRecorder
pyinstaller^
 --add-data "C:\Users\Me\anaconda3\envs\GrimaceRecorder\Lib\site-packages\ultralytics\cfg\default.yaml;./ultralytics/cfg"^
 --add-data "models/camera_identifier.pt;./models"^
 --add-data "models/frame_quality.pt;./models"^
 --add-data "models/face_cropper.pt;./models"^
 --add-data "models/grimace_scorer.pt;./models"^
 --add-data "models/top_pose_estimator.pt;./models"^
 --add-data "models/top_pose_keypoints.txt;./models"^
 --add-data "models/mock_frame_quality_v2.pt;./models"^
 --add-data "models/mock_face_cropper_v2.pt;./models"^
 --add-data "models/mock_grimace_scorer_v2.pt;./models"^
 --add-data "models/mock_top_pose_estimator.pt;./models"^
 --add-data "camera_config/top.pfs;./camera_config"^
 --add-data "camera_config/front.pfs;./camera_config"^
 --add-data "res/logo.png;./res"^
 --add-data "res/logo.ico;./res"^
 --add-data "res/splashscreen.png;./res"^
 --add-data "res/grimace_legend.drawio.png;./res"^
 --onedir^
 --noconsole^
 --name "Grimace Box"^
 --icon "res/logo.ico"^
 main.py -y