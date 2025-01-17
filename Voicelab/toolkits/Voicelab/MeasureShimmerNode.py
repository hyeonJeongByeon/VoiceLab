import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from Voicelab.pipeline.Node import Node
from parselmouth.praat import call
from Voicelab.toolkits.Voicelab.VoicelabNode import VoicelabNode

###################################################################################################
# MEASURE SHIMMER NODE
# WARIO pipeline node for measuring the shimmer of a voice.
###################################################################################################
# ARGUMENTS
# 'voice'   : sound file generated by parselmouth praat
###################################################################################################
# RETURNS
###################################################################################################


class MeasureShimmerNode(VoicelabNode):
    def __init__(self, *args, **kwargs):
        """
        Args:
            *args:
            **kwargs:
        """
        super().__init__(*args, **kwargs)

        self.args = {
            "start_time": 0,   # Positive float or 0
            "end_time": 0,   # Positive float or 0
            "shortest_period": 0.0001,   # Positive number
            "longest_period": 0.02,  # Positive number
            "maximum_period_factor": 1.3,  # Positive number
            "maximum_amplitude": 1.6,  # Positive number
            "Measure PCA": True,
        }

        self.state = {
            "local_shimmer": [],
            "localdb_shimmer": [],
            "apq3_shimmer": [],
            "aqpq5_shimmer": [],
            "apq11_shimmer": [],
            "dda_shimmer": [],
        }

    def end(self, results):
        """
        Args:
            results:
        """
        if self.args["Measure PCA"]:
            pca_results = self.shimmer_pca()
            if pca_results is not None:
                for i, result in enumerate(results):
                    try:
                        results[i][self]["PCA Result"] = float(pca_results[i])
                    except:
                        results[i][self]["PCA Result"] = "Shimmer PCA Failed"
        return results

    ###############################################################################################
    # process: WARIO hook called once for each voice file.
    ###############################################################################################
    def process(self):
        """shimmer"""

        sound = self.args["voice"]
        try:
            pitch_floor = self.args["Pitch Floor"]
            pitch_ceiling = self.args["Pitch Ceiling"]

            point_process: object = call(
                sound, "To PointProcess (periodic, cc)", pitch_floor, pitch_ceiling
            )

            local_shimmer: float = call(
                [sound, point_process],
                "Get shimmer (local)",
                self.args["start_time"],
                self.args["end_time"],
                self.args["shortest_period"],
                self.args["longest_period"],
                self.args["maximum_period_factor"],
                self.args["maximum_amplitude"],
            )

            localdb_shimmer: float = call(
                [sound, point_process],
                "Get shimmer (local_dB)",
                self.args["start_time"],
                self.args["end_time"],
                self.args["shortest_period"],
                self.args["longest_period"],
                self.args["maximum_period_factor"],
                self.args["maximum_amplitude"],
            )

            apq3_shimmer: float = call(
                [sound, point_process],
                "Get shimmer (apq3)",
                self.args["start_time"],
                self.args["end_time"],
                self.args["shortest_period"],
                self.args["longest_period"],
                self.args["maximum_period_factor"],
                self.args["maximum_amplitude"],
            )

            aqpq5_shimmer: float = call(
                [sound, point_process],
                "Get shimmer (apq5)",
                self.args["start_time"],
                self.args["end_time"],
                self.args["shortest_period"],
                self.args["longest_period"],
                self.args["maximum_period_factor"],
                self.args["maximum_amplitude"],
            )

            apq11_shimmer: float = call(
                [sound, point_process],
                "Get shimmer (apq11)",
                self.args["start_time"],
                self.args["end_time"],
                self.args["shortest_period"],
                self.args["longest_period"],
                self.args["maximum_period_factor"],
                self.args["maximum_amplitude"],
            )

            dda_shimmer: float = call(
                [sound, point_process],
                "Get shimmer (dda)",
                self.args["start_time"],
                self.args["end_time"],
                self.args["shortest_period"],
                self.args["longest_period"],
                self.args["maximum_period_factor"],
                self.args["maximum_amplitude"],
            )

            self.state["local_shimmer"].append(local_shimmer)
            self.state["localdb_shimmer"].append(localdb_shimmer)
            self.state["apq3_shimmer"].append(apq3_shimmer)
            self.state["aqpq5_shimmer"].append(aqpq5_shimmer)
            self.state["apq11_shimmer"].append(apq11_shimmer)
            self.state["dda_shimmer"].append(dda_shimmer)

            return {
                "local_shimmer": local_shimmer,
                "localdb_shimmer": localdb_shimmer,
                "apq3_shimmer": apq3_shimmer,
                "aqpq5_shimmer": aqpq5_shimmer,
                "apq11_shimmer": apq11_shimmer,
                "dda_shimmer": dda_shimmer,
            }
        except:
            return {
                "local_shimmer": "Shimmer measurement failed",
                "localdb_shimmer": "Shimmer measurement failed",
                "apq3_shimmer": "Shimmer measurement failed",
                "aqpq5_shimmer": "Shimmer measurement failed",
                "apq11_shimmer": "Shimmer measurement failed",
                "dda_shimmer": "Shimmer measurement failed",
            }

    def shimmer_pca(self):
        try:
            local_shimmer = self.state["local_shimmer"]
            localdb_shimmer = self.state["localdb_shimmer"]
            apq3_shimmer = self.state["apq3_shimmer"]
            aqpq5_shimmer = self.state["aqpq5_shimmer"]
            apq11_shimmer = self.state["apq11_shimmer"]
            dda_shimmer = self.state["dda_shimmer"]

            shimmer_data = pd.DataFrame(
                np.column_stack(
                    [
                        local_shimmer,
                        localdb_shimmer,
                        apq3_shimmer,
                        aqpq5_shimmer,
                        apq11_shimmer,
                        dda_shimmer,
                    ]
                ),
                columns=[
                    "localShimmer",
                    "localdbShimmer",
                    "apq3Shimmer",
                    "apq5Shimmer",
                    "apq11Shimmer",
                    "ddaShimmer",
                ],
            )
            shimmer_data = shimmer_data.dropna()
            # z-score the Shimmer measurements
            measures = [
                "localShimmer",
                "localdbShimmer",
                "apq3Shimmer",
                "apq5Shimmer",
                "apq11Shimmer",
                "ddaShimmer",
            ]
            x = shimmer_data.loc[:, measures].values
            x = StandardScaler().fit_transform(x)
            # Run the PCA
            pca = PCA(n_components=1)
            principal_components = pca.fit_transform(x)
            shimmer_pca_df = pd.DataFrame(
                data=principal_components, columns=["ShimmerPCA"]
            )
            return shimmer_pca_df.values
        except:
            #shimmer_pca_df.values = "Shimmer PCA failed"
            return "Shimmer PCA failed"
