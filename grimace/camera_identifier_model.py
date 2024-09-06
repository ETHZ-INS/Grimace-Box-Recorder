import torch


class CameraIdentifierModel(torch.nn.Module):
    def __init__(self, device="cpu"):
        super(CameraIdentifierModel, self).__init__()

        self.conv_base = torch.nn.Sequential(
            torch.nn.Conv2d(1, 8, kernel_size=3, stride=2),
            torch.nn.ReLU(),
            torch.nn.Identity(),
            torch.nn.Conv2d(8, 16, kernel_size=3, stride=2),
            torch.nn.ReLU(),
            torch.nn.Identity(),
            torch.nn.Conv2d(16, 32, kernel_size=3, stride=2),
            torch.nn.ReLU(),
            torch.nn.Identity(),
            torch.nn.AdaptiveMaxPool2d((1, 1)),
            torch.nn.Flatten(),
            torch.nn.Identity(),
        )

        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(32, 1),
            torch.nn.Sigmoid()
        )

        self.device = device
        self.to(device)
        self.eval()

    def forward(self, x):
        x = x.to(self.device)
        with torch.no_grad():
            conv_out = self.conv_base(x)
        return self.classifier(conv_out)
