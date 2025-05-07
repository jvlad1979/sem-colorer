#!/bin/bash

# Default values
COLORMAP="gnuplot2_r"
NORM_MIN="-0.3"
NORM_MAX="0.65"
OPACITY="0.7"
INPUT_SVG="/home/daniel/work/wisc/sem_colorer/tests/big_seg_base.svg" # Input SVG filename
REGENERATE_JSON="false" # Set to "false" to skip JSON regeneration

# Array of input paths
input_paths=(
    '/home/daniel/work/wisc/-TBD-Bootstrapping-Si-SiGe-quantum-dot-devices/Figure source files/Figure-Problem1/CorrectedInterChannelFlow/voltages.npz'
    '/home/daniel/work/wisc/-TBD-Bootstrapping-Si-SiGe-quantum-dot-devices/Figure source files/Figure-Problem1/CorrectedIntraChannelCutoff/voltages.npz'
    '/home/daniel/work/wisc/-TBD-Bootstrapping-Si-SiGe-quantum-dot-devices/Figure source files/Figure-Problem1/UncorrectedInterChannelFlow/voltages.npz'
    '/home/daniel/work/wisc/-TBD-Bootstrapping-Si-SiGe-quantum-dot-devices/Figure source files/Figure-Problem1/UncorrectedIntraChannelCutoff/voltages.npz'
)

# Loop through the input paths
for i in 0 1 2 3; do
    input_path="${input_paths[$i]}"
    input_dir=$(dirname "$input_path") # Extract the directory
    # Output file names are generated dynamically
    output_json="colors_corrected_inter_${i}.json"
    output_svg="${input_dir}/voltages_colored_SEM_corrected_inter_voltages_${i}.svg" # Save in same dir

    # Process corrected inter-channel voltages (conditional)
    if [ "$REGENERATE_JSON" = "true" ]; then
        sem-colorer npz \
            "$input_path" \
            "$INPUT_SVG" \
            --output "$output_json" \
            --colormap "$COLORMAP" \
            --min "$NORM_MIN" \
            --max "$NORM_MAX" \
            --opacity "$OPACITY"
    else
        echo "Skipping JSON generation for: $input_path"
    fi

    # Color the SVG and export PNG
    sem-colorer color \
        "$INPUT_SVG" \
        -o "$output_svg" \
        -s "$output_json" \
        --png

    echo "Processed: $input_path -> $output_svg"
done

echo "Finished processing all four files."
