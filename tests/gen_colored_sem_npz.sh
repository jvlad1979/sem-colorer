#!/bin/bash

# Default values
COLORMAP="gnuplot2_r"
NORM_MIN="-0.3"
NORM_MAX="0.65"
OPACITY="0.7"

# Process corrected inter-channel voltages
sem-colorer npz \
    "/home/daniel/work/wisc/-TBD-Bootstrapping-Si-SiGe-quantum-dot-devices/Figure source files/Figure-Problem1/CorrectedInterChannelFlow/voltages.npz" \
    "input.svg" \
    --output "colors_corrected_inter.json" \
    --colormap "$COLORMAP" \
    --min "$NORM_MIN" \
    --max "$NORM_MAX" \
    --opacity "$OPACITY"

# Color the SVG and export PNG
sem-colorer color \
    "input.svg" \
    -o "voltages_colored_SEM_corrected_inter_voltages.svg" \
    -s "colors_corrected_inter.json" \
    --png