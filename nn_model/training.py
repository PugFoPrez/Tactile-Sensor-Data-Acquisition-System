#!/usr/bin/env python3
#
# Created by Bruce Davidson - Curtin University ID: 20796033
#
# Created:       16th Sep 2026
# Last Modified: 20th Sep 2026 (Bruce Davidson)
#
# nn_model/training.py
# This script is used for training a contact and force estimation model for the eFlesh sensor.

# Below code has been adapted from the original eFlesh paper
# Code has been adapted using Claude to help parse the originally very dense code
# NN development not a core focus of this thesis

import argparse
import os
import csv
import numpy as np
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm

# NN Parameters
epochs = 1000
batch_size = 64
learning_rate = 1e-3
mag_thresh = 145.1
seed = 0

# IO Parameters
data_folder = "../measurements/"
data_file_prefix = "meas"
out_dir = "artifacts"


class MLP(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, hidden: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(inplace=True),
            nn.Linear(hidden, hidden),
            nn.ReLU(inplace=True),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, x):
        return self.net(x)

# Below class has been modified by Claude from the original. Review in progress
class eFleshDataset(torch.utils.data.Dataset):
    """
    Loads one or more combined eFlesh measurement CSVs of the form:

        X, Y, Z, LoadCell(kg),
        eFlesh1_x, eFlesh1_y, eFlesh1_z,
        eFlesh2_x, eFlesh2_y, eFlesh2_z,
        eFlesh3_x, eFlesh3_y, eFlesh3_z,
        eFlesh4_x, eFlesh4_y, eFlesh4_z,
        eFlesh5_x, eFlesh5_y, eFlesh5_z

    Targets (Y): X, Y, Z, LoadCell(kg).

    Inputs  (X): (X,Y,Z) readings from eFlesh board's five magnetometers.
    """

    TARGET_COLS = ["X", "Y", "Z", "LoadCell(kg)"]

    def __init__(
        self,
        csv_path,
        magnetometer_thresh: float = None,
        x_mean=None, x_std=None,
        y_mean=None, y_std=None,
        normalize_x: bool = True,
        normalize_y: bool = True,):

        self._csv_path = csv_path
        self._magnetometer_thresh = magnetometer_thresh

        # Read in the CSV data
        header = None
        rows = []
        with open(csv_path, "r", newline="") as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if not row:
                    continue
                if i == 0: # Check if this is the first row, if yes then it's the header
                    if header is None:
                        header = row
                    continue
                rows.append([float(v) for v in row])

        # Check for errors in file reading
        if header is None or len(rows) == 0:
            raise ValueError(f"No data rows found in: {self._csv_path}")

        for name in self.TARGET_COLS:
            if name not in header:
                raise ValueError(f"Expected column '{name}' not found in header: {header}")

        # Reformat data
        data = np.asarray(rows, dtype=np.float64)

        col_idx = {name: i for i, name in enumerate(header)}
        target_idx = [col_idx[name] for name in self.TARGET_COLS]
        sensor_idx = [i for i in range(len(header)) if i not in target_idx]

        # Threshold the magnetometer readings
        # i.e., assume that any reading below this value is zero
        # and is due to noise
        # TODO understand the impact of this first
        # if magnetometer_thresh is not None:

        self.header = header
        self.sensor_names = [header[i] for i in sensor_idx]
        self.X = data[:, sensor_idx].astype(np.float32)
        self.Y = data[:, target_idx].astype(np.float32)

        # Normalise data
        self.normalize_x = normalize_x
        self.normalize_y = normalize_y

        # TODO idk what the below is but figure it out
        if self.normalize_x:
            if x_mean is None or x_std is None:
                x_mean = self.X.mean(axis=0)
                x_std = self.X.std(axis=0)
            x_std = np.where(x_std < 1e-8, 1.0, x_std)
            self.x_mean = x_mean.astype(np.float32)
            self.x_std = x_std.astype(np.float32)
            self.X = (self.X - self.x_mean) / self.x_std
        else:
            self.x_mean = np.zeros(self.X.shape[1], dtype=np.float32)
            self.x_std = np.ones(self.X.shape[1], dtype=np.float32)

        if self.normalize_y:
            if y_mean is None or y_std is None:
                y_mean = self.Y.mean(axis=0)
                y_std = self.Y.std(axis=0)
            y_std = np.where(y_std < 1e-8, 1.0, y_std)
            self.y_mean = y_mean.astype(np.float32)
            self.y_std = y_std.astype(np.float32)
            self.Y = (self.Y - self.y_mean) / self.y_std
        else:
            self.y_mean = np.zeros(len(self.TARGET_COLS), dtype=np.float32)
            self.y_std = np.ones(len(self.TARGET_COLS), dtype=np.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]

    def unnormalize_y(self, y):
        if isinstance(y, torch.Tensor):
            return y * torch.tensor(self.y_std, device=y.device) + torch.tensor(self.y_mean, device=y.device)
        return y * self.y_std + self.y_mean

def fit(
    dataset_full: eFleshDataset,
    epochs: int,
    batch_size: int,
    lr: float,
    device: torch.device,
    seed: int = 0):

    # Seed random gen
    torch.manual_seed(seed)
    np.random.seed(seed)

    # Split dataset into random 80% split
    n = len(dataset_full.X)
    idxs = np.arange(n)
    np.random.shuffle(idxs)
    split = int(0.8 * n)
    train_idx, val_idx = idxs[:split], idxs[split:]

    # Compute normalization stats from the training split only
    x_mean = dataset_full.X[train_idx].mean(axis=0)
    x_std = dataset_full.X[train_idx].std(axis=0)
    x_std = np.where(x_std < 1e-8, 1.0, x_std)

    y_mean = dataset_full.Y[train_idx].mean(axis=0)
    y_std = dataset_full.Y[train_idx].std(axis=0)
    y_std = np.where(y_std < 1e-8, 1.0, y_std)

    # Init dataset
    dataset = eFleshDataset(
        csv_path=dataset_full._csv_path,
        magnetometer_thresh=dataset_full._magnetometer_thresh,
        x_mean=x_mean, x_std=x_std,
        y_mean=y_mean, y_std=y_std,
        normalize_x=True, normalize_y=True,
    )

    # Define training and validation dataset loaders
    train_loader = torch.utils.data.DataLoader(
        torch.utils.data.Subset(dataset, train_idx), batch_size=batch_size, shuffle=True
    )
    val_loader = torch.utils.data.DataLoader(
        torch.utils.data.Subset(dataset, val_idx), batch_size=batch_size, shuffle=False
    )

    # Define model parameters
    out_dim = dataset.Y.shape[1]  # X, Y, Z, LoadCell(kg)
    model = MLP(in_dim=dataset.X.shape[1], out_dim=out_dim).to(device)
    opt = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    # Train: loop through epochs
    pbar = tqdm(range(1, epochs + 1), desc="Training", dynamic_ncols=True, position=0)
    metrics_bar = tqdm(total=0, bar_format="{desc}", dynamic_ncols=True, position=1)
    for e in pbar:
        model.train()
        train_loss_sum, train_count = 0.0, 0
        for Xb, Yb in train_loader:
            Xb = Xb.float().to(device)
            Yb = Yb.float().to(device)
            opt.zero_grad()
            pred = model(Xb)
            loss = criterion(pred, Yb)
            loss.backward()
            opt.step()
            train_loss_sum += loss.item() * Xb.size(0)
            train_count += Xb.size(0)
        train_mse = train_loss_sum / max(1, train_count)

        model.eval()
        val_loss_sum, val_count = 0.0, 0
        all_pred, all_true = [], []
        with torch.no_grad():
            for Xb, Yb in val_loader:
                Xb = Xb.float().to(device)
                Yb = Yb.float().to(device)
                pred = model(Xb)
                loss = criterion(pred, Yb)
                val_loss_sum += loss.item() * Xb.size(0)
                val_count += Xb.size(0)
                all_pred.append(pred.cpu())
                all_true.append(Yb.cpu())
        val_mse = val_loss_sum / max(1, val_count)

        pred = torch.cat(all_pred, dim=0)
        true = torch.cat(all_true, dim=0)

        pred_real = torch.from_numpy(dataset.unnormalize_y(pred.numpy()))
        true_real = torch.from_numpy(dataset.unnormalize_y(true.numpy()))
        d = pred_real - true_real

        per_col_rmse = torch.sqrt(torch.mean(d ** 2, dim=0))
        spatial_rmse = torch.sqrt(torch.mean(torch.sum(d[:, :3] ** 2, dim=1)))
        rx, ry, rz, rf = (
            per_col_rmse[0].item(),
            per_col_rmse[1].item(),
            per_col_rmse[2].item(),
            per_col_rmse[3].item(),
        )
        metrics_bar.set_description_str(
            f"Train MSE {train_mse:.4f} | Val MSE {val_mse:.4f} | "
            f"RMSE x {rx:.2f} y {ry:.2f} z {rz:.2f} | Net {spatial_rmse.item():.2f} mm | "
            f"F {rf:.3f} kg"
        )

    metrics_bar.close()
    pbar.close()

    return model, (x_mean, x_std, y_mean, y_std)

def main():
    pattern = os.path.join(f"{data_folder}", f"{data_file_prefix}_*.csv")
    csv_path = sorted(glob.glob(pattern))
    if not csv_path:
        raise FileNotFoundError(f"No measurement files found matching pattern: {pattern}")
    csv_path = csv_path[-1] # get most recent # TODO I DON'T LIKE THIS METHOD OF DOING IT

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    full = eFleshDataset(
        csv_path=csv_path,
        magnetometer_thresh=mag_thresh,
        normalize_x=False,
        normalize_y=False,
    )
    print(f"Loaded {len(full)} samples "
          f"({full.X.shape[1]} sensor inputs -> {full.Y.shape[1]} targets: {full.TARGET_COLS})")

    model, stats = fit(
        dataset_full=full,
        epochs=epochs,
        batch_size=batch_size,
        lr=learning_rate,
        device=device,
        seed=seed,
    )

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"eflesh_{data_file_prefix}_spatial_force_mlp128.pt")

    torch.save(
        {
            "state_dict": model.state_dict(),
            "in_dim": full.X.shape[1],
            "out_dim": full.Y.shape[1],
            "target_names": full.TARGET_COLS,
            "sensor_names": full.sensor_names,
            "magnetometer_thresh": mag_thresh,
            "x_mean": stats[0],
            "x_std": stats[1],
            "y_mean": stats[2],
            "y_std": stats[3],
        },
        out_path,
    )
    print(f"Saved model to {out_path}")

if __name__ == "__main__":
    main()