import json
import multiprocessing
import os
import inspect
from dataclasses import dataclass, asdict

from scripts.midi_to_dtx import DtxInfo

class JsonConfig:
    def to_dict(self):
        return self.__dict__

    @classmethod
    def get_config_name(cls):
        return "config.json"

    @classmethod
    def get_config_path(cls, config_dir):
        return os.path.join(config_dir, cls.get_config_name())

    @classmethod
    def get_default_config_path(cls):
        return ""

    @classmethod
    def get_default_config(cls):
        config_path = cls.get_default_config_path()
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_json = json.load(f)
                config = cls.from_dict(config_json)
                return config
        return cls()

    @classmethod
    def from_dict(cls, dict):
        return cls(**{
            k: v for k, v in dict.items()
            if k in inspect.signature(cls).parameters
        })

    @classmethod
    def load(cls, config_dir):
        config_path = cls.get_config_path(config_dir)
        if not os.path.exists(config_path):
            config_path = cls.get_default_config_path()
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_json = json.load(f)
                config = cls.from_dict(config_json)
                return config
        return cls()

    def save(self, config_dir):
        if not os.path.exists(config_dir):
            raise Exception("Project path not exists.")
        config_path = self.get_config_path(config_dir)
        with open(config_path, "w") as f:
            json.dump(asdict(self), f, indent=2)

cpu_count = multiprocessing.cpu_count()

@dataclass
class ProjectConfig(JsonConfig):
    bgm_name: str = "bgm.ogg"

    movie_url: str = ""
    movie_download_file_name: str = "source.mp4"
    movie_output_file_name: str = "movie.mp4"
    movie_thumbnail_file_name: str = "pre.jpg"
    movie_start_time: float = 0.0
    movie_end_time: float = 0.0
    movie_width: int = 0
    movie_height: int = 0

    preview_output_name: str = "pre.ogg"
    preview_start_time: float = 0.0
    preview_duration: float = 20.0
    preview_fade_in_duration: float = 1.0
    preview_fade_out_duration: float = 5.0

    separate_model: str = "htdemucs"
    separate_jobs: int = cpu_count

    midi_input_name: str = "drums.wav"
    midi_resolution: int = 8
    midi_threshold: float = 0.2
    midi_segmentation: float = 0.9
    midi_adjust_velocity: float = 0.3

    bd_min: int = 36 # C1
    sn_min: int = 53 # F2
    ht_min: int = 46 # A#1
    lt_min: int = 41 # F1
    ft_min: int = 0

    bd_range: int = 4
    sn_range: int = 4
    ht_range: int = 4
    lt_range: int = 4
    ft_range: int = 0

    dtx_input_name: str = "drums.mid"
    dtx_output_name: str = "score.dtx"
    dtx_output_image_name: str = "score.png"
    dtx_bpm: float = 120.0
    dtx_chip_resolution: int = 32
    dtx_bgm_resolution: int = 128
    dtx_shift_time: float = 0
    dtx_auto_shift_time: bool = True
    dtx_align_nth_bd: int = 1
    dtx_auto_align_nth_bd: bool = True
    dtx_bgm_offset_time: float = -0.03
    dtx_bgm_volume: int = 100
    dtx_wav_splits: int = 4
    dtx_wav_volume: int = 80
    dtx_show_image: bool = False

    dtx_title: str = "Sample Music"
    dtx_artist: str = ""
    dtx_comment: str = ""
    dtx_dlevel: int = 50

    hhc_wav: str = "chips\\close.xa"
    snare_wav: str = "chips\\snare.xa"
    bd_wav: str = "chips\\bd.xa"
    ht_wav: str = "chips\\high.xa"
    lt_wav: str = "chips\\low.xa"
    cymbal_wav: str = "chips\\cymbal.xa"
    ft_wav: str = "chips\\floor.xa"
    hho_wav: str = "chips\\open.xa"
    ride_wav: str = "chips\\ride.xa"
    lc_wav: str = "chips\\lc.xa"
    lp_wav: str = "chips\\lp.xa"
    lbd_wav: str = "chips\\lbd.xa"

    hhc_volume: int = 100
    snare_volume: int = 100
    bd_volume: int = 100
    ht_volume: int = 100
    lt_volume: int = 100
    cymbal_volume: int = 100
    ft_volume: int = 100
    hho_volume: int = 100
    ride_volume: int = 100
    lc_volume: int = 100
    lp_volume: int = 100
    lbd_volume: int = 100

    hhc_offset: float = 0.0
    snare_offset: float = 0.0
    bd_offset: float = 0.03
    ht_offset: float = 0.0
    lt_offset: float = 0.0
    cymbal_offset: float = 0.0
    ft_offset: float = 0.0
    hho_offset: float = 0.0
    ride_offset: float = 0.0
    lc_offset: float = 0.0
    lp_offset: float = 0.0
    lbd_offset: float = 0.0

    @classmethod
    def get_config_name(cls):
        return "tube_dtx_config.json"

    @classmethod
    def get_default_config_path(cls):
        return os.path.join("resources", cls.get_config_name())

    def get_dtx_info(self):
        return DtxInfo(
            TITLE = self.dtx_title,
            ARTIST = self.dtx_artist,
            COMMENT = self.dtx_comment,
            PREVIEW = self.preview_output_name,
            PREIMAGE = self.movie_thumbnail_file_name,
            BGM = self.bgm_name,
            VIDEO = self.movie_output_file_name,
            BPM = self.dtx_bpm,
            DLEVEL = self.dtx_dlevel,

            HHC_WAV = self.hhc_wav,
            SNARE_WAV = self.snare_wav,
            BD_WAV = self.bd_wav,
            HT_WAV = self.ht_wav,
            LT_WAV = self.lt_wav,
            CYMBAL_WAV = self.cymbal_wav,
            FT_WAV = self.ft_wav,
            HHO_WAV = self.hho_wav,
            RIDE_WAV = self.ride_wav,
            LC_WAV = self.lc_wav,
            LP_WAV = self.lp_wav,
            LBD_WAV = self.lbd_wav,

            HHC_VOLUME = self.hhc_volume,
            SNARE_VOLUME = self.snare_volume,
            BD_VOLUME = self.bd_volume,
            HT_VOLUME = self.ht_volume,
            LT_VOLUME = self.lt_volume,
            CYMBAL_VOLUME = self.cymbal_volume,
            FT_VOLUME = self.ft_volume,
            HHO_VOLUME = self.hho_volume,
            RIDE_VOLUME = self.ride_volume,
            LC_VOLUME = self.lc_volume,
            LP_VOLUME = self.lp_volume,
            LBD_VOLUME = self.lbd_volume,

            HHC_OFFSET = self.hhc_offset,
            SNARE_OFFSET = self.snare_offset,
            BD_OFFSET = self.bd_offset,
            HT_OFFSET = self.ht_offset,
            LT_OFFSET = self.lt_offset,
            CYMBAL_OFFSET = self.cymbal_offset,
            FT_OFFSET = self.ft_offset,
            HHO_OFFSET = self.hho_offset,
            RIDE_OFFSET = self.ride_offset,
            LC_OFFSET = self.lc_offset,
            LP_OFFSET = self.lp_offset,
            LBD_OFFSET = self.lbd_offset,

            CHIP_RESOLUTION = self.dtx_chip_resolution,
            BGM_RESOLUTION = self.dtx_bgm_resolution,
            SHIFT_TIME = self.dtx_shift_time,
            AUTO_SHIFT_TIME = self.dtx_auto_shift_time,
            ALIGN_NTH_BD = self.dtx_align_nth_bd,
            BGM_OFFSET_TIME = self.dtx_bgm_offset_time,
            BGM_VOLUME = self.dtx_bgm_volume,
            AUTO_ALIGN_NTH_BD = self.dtx_auto_align_nth_bd,
            WAV_SPLITS = self.dtx_wav_splits,
            WAV_VOLUME = self.dtx_wav_volume,
        )

    def get_resources(self):
        return [
            self.hhc_wav,
            self.snare_wav,
            self.bd_wav,
            self.ht_wav,
            self.lt_wav,
            self.cymbal_wav,
            self.ft_wav,
            self.hho_wav,
            self.ride_wav,
            self.lc_wav,
            self.lp_wav,
            self.lbd_wav,
        ]

@dataclass
class AppConfig(JsonConfig):
    project_path: str = ""
    workspace_path: str = ""
    auto_save: bool = True

    def get_project_paths(self):
        if not os.path.isdir(self.workspace_path):
            return []

        files = os.listdir(self.workspace_path)
        project_paths = [os.path.join(self.workspace_path, f) for f in files if os.path.isdir(os.path.join(self.workspace_path, f))]
        return project_paths

    @classmethod
    def get_preimage(cls, project_path):
        preimage = os.path.join(project_path, "pre.jpg")
        if not os.path.exists(preimage):
            preimage = os.path.join("resources", "pre.jpg")
        return preimage

    def get_current_preimage(self):
        return AppConfig.get_preimage(self.project_path)

    @classmethod
    def get_movie(cls, project_path):
        movie_path = os.path.join(project_path, "movie.mp4")
        if not os.path.exists(movie_path):
            movie_path = None
        return movie_path

    def get_current_movie(self):
        return AppConfig.get_movie(self.project_path)

    def get_all_preimages(self):
        project_paths = self.get_project_paths()
        preimages = [AppConfig.get_preimage(f) for f in project_paths]
        return preimages

    def get_all_gallery(self):
        project_paths = self.get_project_paths()
        gallery = [(AppConfig.get_preimage(f), os.path.basename(f)) for f in project_paths]
        return gallery

app_config = AppConfig.load(".")
