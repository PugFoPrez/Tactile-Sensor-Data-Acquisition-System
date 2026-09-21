#!/usr/bin/env python3
#
# Created by Bruce Davidson - Curtin University ID: 20796033
#
# Created:       20th Sep 2026
# Last Modified: 20th Sep 2026 (Bruce Davidson)
#
# nn_model/testing.py
# This script loads a trained contact and force estimation model for the eFlesh sensor
# (saved by training.py) and evaluates it on a separate testing dataset.
#
# Expects the testing CSV to be formatted identically to the measurement CSVs
# used for training, and named "testing_<DATETIME>.csv"
# e.g. "testing_2026-09-16 17:38:19.csv"
#
# Usage:
#   python testing.py                          # latest testing_*.csv + default model
#   python testing.py --csv "../measurements/testing_2026-09-16 17:38:19.csv"
#   python testing.py --model artifacts/some_other_model.pt

# WARNING: This file has been generated using Claude AI - To be reviewed

import argparse
import os
import glob
import json
import numpy as np
import torch
import torch.nn as nn

from training import MLP, eFleshDataset

# IO Parameters (keep the same as in training.py)
data_folder = "../measurements/"
test_file_prefix = "testing"
data_file_prefix = "meas"
out_dir = "artifacts"
model_file = f"eflesh_{data_file_prefix}_spatial_force_mlp128.pt"

# Eval Parameters
batch_size = 1024


def load_model(model_path: str, device: torch.device):
    # weights_only=False because the checkpoint contains numpy arrays (normalisation stats)
    # Only load checkpoints that you created yourself
    ckpt = torch.load(model_path, map_location=device, weights_only=False)

    # Infer hidden width from the saved weights rather than assuming the default
    hidden = ckpt["state_dict"]["net.0.weight"].shape[0]
    model = MLP(in_dim=ckpt["in_dim"], out_dim=ckpt["out_dim"], hidden=hidden).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, ckpt


def evaluate(model: nn.Module, dataset: eFleshDataset, device: torch.device):
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
    criterion = nn.MSELoss()

    loss_sum, count = 0.0, 0
    all_pred, all_true = [], []
    with torch.no_grad():
        for Xb, Yb in loader:
            Xb = Xb.float().to(device)
            Yb = Yb.float().to(device)
            pred = model(Xb)
            loss = criterion(pred, Yb)
            loss_sum += loss.item() * Xb.size(0)
            count += Xb.size(0)
            all_pred.append(pred.cpu())
            all_true.append(Yb.cpu())

    # MSE in normalised space (equivalent to "Val MSE" in training.py)
    test_mse = loss_sum / max(1, count)

    pred = torch.cat(all_pred, dim=0)
    true = torch.cat(all_true, dim=0)

    # Convert back to real units (mm for X/Y/Z, kg for load cell)
    pred_real = torch.from_numpy(dataset.unnormalize_y(pred.numpy()))
    true_real = torch.from_numpy(dataset.unnormalize_y(true.numpy()))
    d = pred_real - true_real

    per_col_rmse = torch.sqrt(torch.mean(d ** 2, dim=0))
    spatial_rmse = torch.sqrt(torch.mean(torch.sum(d[:, :3] ** 2, dim=1)))

    return {
        "n_samples": count,
        "test_mse": test_mse,
        "rmse_x": per_col_rmse[0].item(),
        "rmse_y": per_col_rmse[1].item(),
        "rmse_z": per_col_rmse[2].item(),
        "rmse_3d_mm": spatial_rmse.item(),
        "rmse_force_kg": per_col_rmse[3].item(),
    }


def find_latest_test_csv() -> str:
    pattern = os.path.join(data_folder, f"{test_file_prefix}_*.csv")
    files = sorted(glob.glob(pattern))  # datetime in the name sorts chronologically
    if not files:
        raise FileNotFoundError(f"No testing files found matching pattern: {pattern}")
    return files[-1]


def main():
    parser = argparse.ArgumentParser(description="Evaluate a trained eFlesh model on a testing CSV.")
    parser.add_argument("--csv", default=None, help="Path to testing CSV (default: latest testing_*.csv)")
    parser.add_argument("--model", default=os.path.join(out_dir, model_file), help="Path to saved model .pt")
    args = parser.parse_args()

    csv_path = args.csv if args.csv else find_latest_test_csv()
    if not os.path.isfile(args.model):
        raise FileNotFoundError(f"Model file not found: {args.model}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, ckpt = load_model(args.model, device)

    # Load the test set, normalised using the TRAINING statistics saved in the checkpoint
    dataset = eFleshDataset(
        csv_path=csv_path,
        magnetometer_thresh=ckpt.get("magnetometer_thresh"),
        x_mean=np.asarray(ckpt["x_mean"]), x_std=np.asarray(ckpt["x_std"]),
        y_mean=np.asarray(ckpt["y_mean"]), y_std=np.asarray(ckpt["y_std"]),
        normalize_x=True, normalize_y=True,
    )

    # Sanity checks: the test CSV must have the same layout the model was trained on
    if dataset.sensor_names != list(ckpt["sensor_names"]):
        raise ValueError(
            f"Sensor columns differ from training.\n"
            f"  Model:   {ckpt['sensor_names']}\n"
            f"  Testing: {dataset.sensor_names}"
        )
    if list(dataset.TARGET_COLS) != list(ckpt["target_names"]):
        raise ValueError("Target columns differ from those used in training.")

    print(f"Model:   {args.model}")
    print(f"Testing: {csv_path}")
    print(f"Loaded {len(dataset)} samples "
          f"({dataset.X.shape[1]} sensor inputs -> {dataset.Y.shape[1]} targets: {dataset.TARGET_COLS})")

    m = evaluate(model, dataset, device)

    # Same format as the training script's metrics bar
    print(
        f"Test MSE {m['test_mse']:.4f} | "
        f"RMSE x {m['rmse_x']:.2f} y {m['rmse_y']:.2f} z {m['rmse_z']:.2f} | "
        f"3D RMSE {m['rmse_3d_mm']:.2f} mm | "
        f"F {m['rmse_force_kg']:.3f} kg"
    )

    # Record metrics to disk
    os.makedirs(out_dir, exist_ok=True)
    safe_stem = os.path.splitext(os.path.basename(csv_path))[0].replace(" ", "_").replace(":", "-")
    metrics_path = os.path.join(out_dir, f"metrics_{safe_stem}.json")
    with open(metrics_path, "w") as f:
        json.dump({"model": args.model, "test_file": csv_path, **m}, f, indent=2)
    print(f"Saved metrics to {metrics_path}")


if __name__ == "__main__":
    main()