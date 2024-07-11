from typing import Union

import numpy as np
import timm
import torch


class FrameQualityModel(torch.nn.Module):
    def __init__(self, device="cuda"):
        super(FrameQualityModel, self).__init__()
        print("Loading model")
        self.base_model = timm.create_model("mobilenetv3_large_100", in_chans=1, pretrained=False)

        base_model_output = self.base_model(torch.zeros(1, 1, 224, 224))
        num_features = base_model_output.shape[1]

        self.score_head = torch.nn.Sequential(
            torch.nn.Identity(),
            torch.nn.Linear(num_features, 1),
            torch.nn.Sigmoid()
        )

        self.device = device
        self.to(device)
        self.eval()

    def forward(self, x: Union[torch.Tensor, np.ndarray]):
        x = x.to(self.device)
        with torch.no_grad():
            out = self.base_model(x)
            out = self.score_head(out)
        return out
