# AUDIU
# recommendations.py

import os
import json
import time
import pathlib

## RECOMMENDATIONS CLASS ##
# recommendations model wrapper class
class Recommendations():

    ## RECOMMENDATIONS ML MODEL ##

    ## static methods ##
    # process fork for generating recommendations
    @staticmethod
    def recommendations_run(run_id, model_run_src, model_run_signal_queue):
        model_run_signal_queue.put("main:run-start:{}".format(run_id))
        package_dir_path = os.path.dirname(os.path.abspath(__file__))
        model_run_dir_path = os.path.join(package_dir_path, model_run_src)
        model_run_path = pathlib.Path(os.path.join(model_run_dir_path, run_id))
        input_data_json = None
        with open(model_run_path / 'input.json', 'r') as f:
            input_data_json = json.load(f)
        model_type = input_data_json["model_type"]
        target_playlists = input_data_json["target_playlists"]
        reject_playlists = input_data_json["reject_playlists"]
        inference_playlists = input_data_json["inference_playlists"]
        input_data = {
            "run_id": run_id,
            "model_type": model_type,
            "target_playlists": target_playlists,
            "reject_playlists": reject_playlists,
            "inference_playlists": inference_playlists
        }
        print("[ml] generating recommendations for run {}".format(run_id))
        # print(input_data)
        results, ts_profile = Recommendations.generate_recommendations(
            run_id, model_type, target_playlists, reject_playlists, inference_playlists)
        output_data = {
            "run_id": run_id,
            "model_type": model_type,
            "results": results,
            "ts_profile": {
                "ts_total_length": ts_profile[0],
                "ts_training_length": ts_profile[1],
                "ts_inference_length": ts_profile[2]
            }
        }
        with open(model_run_path / 'output.json', 'w') as f:
            json.dump(output_data, f, indent=4, sort_keys=False)
        model_run_signal_queue.put("main:run-done:{}".format(run_id))
    # generate recommendations
    @staticmethod
    def generate_recommendations(run_id, model_type, target_playlists, reject_playlists, inference_playlists):
        # TODO: actually generate recommendations using ml models
        results = []
        # training
        ts_training_start = time.time()
        for i in range(10):
            print("[ml] run {}: training - sample epoch {}".format(run_id, i))
            time.sleep(0.5)
        ts_training_end = time.time()
        ts_training_length = ts_training_end - ts_training_start
        # inference
        ts_inference_start = time.time()
        for i in range(10):
            print("[ml] run {}: inference - sample epoch {}".format(run_id, i))
            results.append(str(i))
            time.sleep(0.25)
        ts_inference_end = time.time()
        ts_inference_length = ts_inference_end - ts_inference_start
        ts_total_length = ts_training_length + ts_inference_length
        # return data
        return (results, (ts_total_length, ts_training_length, ts_inference_length))

    # instance fields
    dataset_src = ''
    dataset = None
    package_dir_path = None
    model_run_src = None
    model_run_dir_path = None
    # constructor
    def __init__(self, dataset_src='dataset.json', model_run_src='data/runs'):
        self.dataset = {}
        self.model_run_src = model_run_src
        self.package_dir_path = os.path.dirname(os.path.abspath(__file__))
        self.dataset_src = os.path.join(self.package_dir_path, dataset_src)
        self.model_run_dir_path = os.path.join(
            self.package_dir_path, model_run_src)

    # load local dataset
    def load_dataset(self):
        playlists = None
        genres = None
        config = None
        models = None
        with open(self.dataset_src) as dataset_file:
            dataset_json = json.load(dataset_file)
            playlists = dataset_json['playlists']
            genres = dataset_json['genres']
            models = dataset_json['models']
            config = dataset_json['config']
        self.dataset['playlists'] = playlists
        self.dataset['genres'] = genres
        self.dataset['models'] = models
        self.dataset['config'] = config

    # convert genre list to playlist using local dataset
    def genres_to_playlists(self, genres_list, return_slugs=True):
        playlist_id_list = []
        playlist_slug_list = []
        for genre in genres_list:
            playlist_slug_list.extend(self.dataset['genres'][genre])
        playlist_slug_list = list(set(playlist_slug_list))
        # print(playlist_slug_list)
        for slug in playlist_slug_list:
            playlist_id_list.append(self.dataset['playlists'][slug])
        playlist_id_list = list(set(playlist_id_list))
        # print(playlist_id_list)
        if return_slugs:
            return (playlist_id_list, playlist_slug_list)
        return playlist_id_list

    # invert list of genres with dataset
    def genre_set_invert(self, genres_list):
        genres_inverse = []
        for genre in self.dataset['genres'].keys():
            if genre not in genres_list and genre != self.dataset['config']['genre_remove_item']:
                genres_inverse.append(genre)
        return genres_inverse

    # prep method before process fork for generating recommendations
    def recommendations_prepare_input(self, run_id):
        model_run_path = pathlib.Path(os.path.join(self.model_run_dir_path, run_id))
        model_run_path.mkdir(parents=True, exist_ok=True)
        request_json = None
        with open(model_run_path / 'request.json', 'r') as f:
            request_json = json.load(f)
        request_data = {
            "run_id": run_id,
            "selected_model": request_json['selected_model'],
            "playlist_selections": request_json['playlist_selections'],
            "genre_selections": request_json['genre_selections']
        }
        # # data preprocessing
        model_type = request_data["selected_model"]
        target_playlists = request_data['playlist_selections']
        reject_playlists = self.genres_to_playlists(
            self.genre_set_invert(request_data['genre_selections']), False)
        inference_playlists = self.genres_to_playlists(
            request_data['genre_selections'], False)
        input_data = {
            "run_id": run_id,
            "model_type": model_type,
            "target_playlists": target_playlists,
            "reject_playlists": reject_playlists,
            "inference_playlists": inference_playlists
        }
        with open(model_run_path / 'input.json', 'w') as f:
            json.dump(input_data, f, indent=4, sort_keys=False)
        
