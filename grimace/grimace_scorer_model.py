import torch
from torchvision.models import vit_b_16, ViT_B_16_Weights


class GrimaceScoreModel(torch.nn.Module):
    def __init__(self, device="cuda"):
        super(GrimaceScoreModel, self).__init__()

        self.device = device

        self.base_model = vit_b_16(weights=None)
        self.base_model.heads = torch.nn.Identity()

        base_model_output = self.base_model(torch.zeros(1, 3, 224, 224))
        num_features = base_model_output.shape[1]

        input_size = num_features

        self.hidden_layers = torch.nn.Sequential()

        hidden_layer_sizes = [2048, 1024]

        for hidden_layer_size in hidden_layer_sizes:
            self.hidden_layers.append(torch.nn.Sequential(
                torch.nn.Dropout(0.0),
                torch.nn.Linear(input_size, hidden_layer_size),
                torch.nn.ReLU(),
            ))
            input_size = hidden_layer_size

        self.au_heads = torch.nn.ModuleList()

        for _ in range(5):
            self.au_heads.append(torch.nn.Sequential(
                torch.nn.Linear(input_size, 4)
            ))

        self.to(device)
        self.eval()

    def forward(self, x):
        x = x.to(self.device)
        with torch.no_grad():
            out = self.base_model(x)
            out = self.hidden_layers(out)
            out = [head(out) for head in self.au_heads]
            out = torch.concat(out, dim=1)
        out = out.softmax(dim=1)
        out = out.reshape(out.shape[0], 5, 4)
        return out
