import numpy as np
from pathlib import Path
from datetime import datetime
from spacepy import pycdf
import re
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import PowerNorm

TOF3_L = [11.0, 7.0, 3.5, 0.0]
TOF3_H = [15.0, 11.0, 7.0, 3.5]
# TOF_0, TOF_1, TOF_2
E_PEAK_H = [20.0, 10.0, 10.0]
H_PEAK_L = [20.0, 10.0, 10.0]
H_PEAK_H = [70.0, 50.0, 40.0]
CO_PEAK_L = [100.0, 60.0, 60.0]
CO_PEAK_H = [270.0, 150.0, 150.0]
#  for GOLD, TOF2 < 15, TOF2 < 35 and > 35

# EU = C0 + C1 * ADC
# ADC_TOF = [C0, C1]
ADC_TOF0 = [5.5252E-01, 1.6837E-01]
ADC_TOF1 = [-7.2018E-01, 1.6512E-01]
ADC_TOF2 = [3.7442E-01, 1.6641E-01]
ADC_TOF3 = [4.6726E-01, 1.7144E-01]

CHKSM_LB = -21
CHKSM_RB = -6

PI = np.pi

epoch0 = datetime(2010, 1, 1, 0, 0, 0)

cols = ['shcoarse', 'absent', 'timestamp', 'egy', 'mode', 'TOF0', 'TOF1', 'TOF2',
        'TOF3', 'checksum', 'position']


def doy_fraction(t):
    start = datetime(t.year, 1, 1)
    return (t - start).total_seconds() / 86400.0 + 1


def remap_spin_bins(h):
    return np.concatenate(
        (h[:, :, 50:60], h[:, :, 0:20], h[:, :, 20:50]),
        axis=2
    )


def met_from_epoch(t: datetime):
    dt = t - datetime(2010, 1, 1, 0, 0, 0)
    return dt.total_seconds() + 9


epoch = datetime(2010, 1, 1, 0, 0, 0)


def process(hist_cdf: Path, ncycle_sum: int, output_dir: Path):
    cdf = pycdf.CDF(str(hist_cdf))
    date = re.search(r"\d{8}", hist_cdf.stem).group()
    epoch = cdf['epoch'][...]

    for var in ('h_counts', 'o_counts'):

        counts = cdf[var][...]
        vmax1 = max([np.max(d) for d in counts])

        # Summed diagnostic (your exact line)
        d = np.sum(counts[:, 0:6, 20:49], axis=(1, 2))

        total = np.sum(d)

        # ------------------------------------------------------------
        # Convert epoch -> MET seconds (relative to first sample)
        # ------------------------------------------------------------
        met = np.array([(t - epoch[0]).total_seconds() for t in epoch])

        t0 = epoch[0]  # your starting datetime

        start_doy = t0.timetuple().tm_yday \
                    + t0.hour / 24 \
                    + t0.minute / (24 * 60) \
                    + t0.second / (24 * 3600) \
                    + t0.microsecond / (24 * 3600 * 1e6)

        doy = start_doy + met / (24 * 3600)  # 24*3600 = seconds per day

        # ------------------------------------------------------------
        # Build ESA heatmaps: (spin_bin, time)
        # ------------------------------------------------------------
        n_esa = 7

        h_cnt_nep = remap_spin_bins(counts)

        esa_maps = [h_cnt_nep[:, i, :].T for i in range(n_esa)]
        spin_bins = np.arange(h_cnt_nep.shape[2])

        # ------------------------------------------------------------
        # FIGURE + GRIDSPEC LAYOUT
        # ------------------------------------------------------------
        fig = plt.figure(figsize=(15, 10))

        gs = GridSpec(
            n_esa + 1, 2,
            width_ratios=[30, 1],  # plots | colorbar
            height_ratios=[1] + [1] * n_esa,
            hspace=0.08,
            wspace=0.05
        )

        # Left column axes
        axes = [fig.add_subplot(gs[i, 0]) for i in range(n_esa + 1)]

        # Right column colorbar axis (ESA panels only)
        cax = fig.add_subplot(gs[1:, 1])

        # ------------------------------------------------------------
        # TOP PANEL: summed diagnostic
        # ------------------------------------------------------------
        axes[0].plot(doy, d, linewidth=1)
        axes[0].set_ylabel("Summed \nARam \nCounts", fontsize=12)
        axes[0].grid(True, alpha=0.3)

        # ------------------------------------------------------------
        # ESA HEATMAP PANELS
        # ------------------------------------------------------------
        im = None
        for i in range(n_esa):
            ax = axes[i + 1]

            norm = PowerNorm(gamma=0.15, vmin=0.0, vmax=vmax1)

            im = ax.imshow(
                esa_maps[i],
                aspect='auto',
                origin='lower',
                extent=[
                    doy.min(), doy.max(),
                    spin_bins.min(), spin_bins.max()
                ],
                #        vmin=0,
                #       vmax=vmax,
                norm=norm
            )

            ax.set_ylabel(f"ESA {i + 1}\nNEP", fontsize=14)
            ax.set_yticks([0, spin_bins.max()])
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.tick_params(axis='x', labelsize=12)  # increase x-axis tick label size
            ax.tick_params(axis='y', labelsize=12)

        # ------------------------------------------------------------
        # COLORBAR (off to the side)
        # ------------------------------------------------------------
        cbar = fig.colorbar(im, cax=cax)
        cbar.set_label("Counts", fontsize=14)
        cbar.ax.tick_params(labelsize=14)
        cbar.ax.yaxis.labelpad = 10

        # ------------------------------------------------------------
        # LABELS + TITLE (with breathing room)
        # ------------------------------------------------------------
        axes[-1].set_xlabel("DOY ", fontsize=14)

        fig.suptitle(
            f"IMAP-Lo {date} {var} total ARam = {total}",
            fontsize=16,
            y=0.97
        )

        fig.subplots_adjust(
            left=0.08,
            right=0.92,
            top=0.90,
            bottom=0.06
        )

        plt.savefig(f"{output_dir}/{hist_cdf.stem}_{var}.png", dpi=200)
        plt.close()


if __name__ == "__main__":
    process(
        Path("/media/vineetb/T7/imap/lo/l1b/2026/04/imap_lo_l1b_histrates_20260413-repoint00217_v002.cdf"),
        10,
        Path("output")
    )

