from typing import Optional

from app.config.video_files import VideoFilesConfig


class VideoFilesValidator:
    @classmethod
    def _validate(cls, video_files: VideoFilesConfig) -> Optional[str]:
        if video_files is None:
            return "Config is null"

        naming_mode = video_files.naming_mode

        if naming_mode is None:
            return "Naming mode is null"

        if naming_mode not in video_files.NAMING_MODES:
            return "Naming mode is invalid, must be one of: " + ", ".join(video_files.NAMING_MODES)

        top_template = video_files.top_templates.get(naming_mode)
        front_template = video_files.front_templates.get(naming_mode)
        grimace_template = video_files.grimace_results_templates.get(naming_mode)

        if top_template is None or top_template == "":
            return "Top video template is not configured correctly"

        if front_template is None or front_template == "":
            return "Front video template is not configured correctly"

        if grimace_template is None or grimace_template == "":
            return "Grimace results template is not configured correctly"

        # Make sure the templates are different
        # The names of the variables that make the filenames unique (recording_number and start_time) are replaced with
        # {unique_var} so just switching the variable names would not be enough
        # as in theory two different variables could contain the same value and still lead to duplicate file names
        def simplify(template):
            template = template.replace("{recording_number}", "{unique_var}")
            template = template.replace("{start_time}", "{unique_var}")
            return template

        top_template = simplify(top_template)
        front_template = simplify(front_template)
        grimace_template = simplify(grimace_template)

        if "{unique_var}" not in top_template or "{unique_var}" not in front_template or "{unique_var}" not in grimace_template:
            return ("The templates for the video and grimace results files must contain at least one of the "
                    "variables {recording_number} or {start_time}")

        if top_template == front_template or top_template == grimace_template or front_template == grimace_template:
            return "The templates for the video and grimace results files must be different"

    @classmethod
    def validate(cls, video_files: VideoFilesConfig) -> Optional[str]:
        try:
            return cls._validate(video_files)
        except Exception as e:
            return str(e)
