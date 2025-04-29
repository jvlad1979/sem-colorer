import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
import json
from pathlib import Path
import matplotlib.colors as mcolors
from matplotlib.cm import ScalarMappable
import subprocess

import numpy as np

def get_voltages_from_npz(npz_file: str | Path) -> dict:
    """Get voltages from NPZ file."""
    data = np.load(npz_file)
    return {key: float(data[key]) for key in data.keys()}

def map_suffixless_to_suffixed(original_dict: dict, all_keys: list[str]) -> dict:
    """Maps values from suffixless keys to suffixed keys."""
    new_dict = {}
    suffixes = ["_l", "_r", "_full", ""]

    for key, value in original_dict.items():
        base_key = key.split('_')[0]
        if base_key in [k.split('_')[0] for k in all_keys if '_' in k] or base_key in [k for k in all_keys if '_' not in k]:
            for suffix in suffixes:
                new_key = base_key + suffix
                if new_key in all_keys:
                    new_dict[new_key] = float(value)
    return new_dict

def generate_color_spec_from_npz(
    npz_file: str | Path,
    svg_file: str | Path,
    colormap: str = "viridis",
    norm_range: tuple[float, float] = (0, 1),
    opacity: float = 0.7
) -> dict:
    """Generate color specification from NPZ file."""
    gates = get_svg_gates(svg_file)
    voltages = get_voltages_from_npz(npz_file)
    mapped_voltages = map_suffixless_to_suffixed(voltages, gates)
    
    return {
        "colormap": colormap,
        "norm_range": list(norm_range),
        "gate_colors": {
            gate: {
                "value": mapped_voltages.get(gate, 0.5),
                "opacity": opacity
            } for gate in gates
        }
    }


def get_svg_gates(svg_path: str | Path) -> list[str]:
    """Extract gate names from SVG file."""
    with open(svg_path) as file:
        svg_content = file.read()

    soup = BeautifulSoup(svg_content, "xml")
    paths = soup.find_all("path", attrs={"inkscape:label": True})
    gates = [path.get("inkscape:label") for path in paths]
    return sorted(list(set(gates)))


def load_color_spec(json_path):
    with open(json_path) as f:
        spec = json.load(f)
    return spec


def svg_gate_colorer(
    svg_origin: str | Path,
    svg_target: str | Path | None = None,
    color_spec: str | dict | None = None,
    fill_opacity: float = 0.5,
    export_png: bool = False,
    png_size: tuple[int, int] | None = None
):
    """
    Color an SVG file based on specifications.

    Args:
        svg_origin: Path to source SVG file
        svg_target: Path for output SVG (if None, will append '_colored' to origin name)
        color_spec: Either path to JSON file or dict with color specifications
        fill_opacity: Default opacity for elements without specified opacity
        export_png: If True, also export a PNG version
        png_size: Tuple of (width, height) for PNG export. If None, uses SVG size.
    """
    # Handle paths
    svg_origin = Path(svg_origin)
    if svg_target is None:
        svg_target = svg_origin.parent / f"{svg_origin.stem}_colored{svg_origin.suffix}"
    else:
        svg_target = Path(svg_target)

    # Load color specifications
    if isinstance(color_spec, str):
        spec = load_color_spec(color_spec)
    elif isinstance(color_spec, dict):
        spec = color_spec
    else:
        raise ValueError("color_spec must be either a path to JSON file or a dict")

    # Extract colormap settings
    cmap = spec.get("colormap", "viridis")
    norm_range = spec.get("norm_range", [0, 1])
    gate_colors = spec.get("gate_colors", {})

    # Create color mapper
    norm = Normalize(vmin=norm_range[0], vmax=norm_range[1])
    sm = ScalarMappable(cmap=cmap, norm=norm)
    with open(svg_origin) as file:
        svg_content = file.read()
    # gates = ["R1","S1_l","B1","P1","B2","P2","B3","P3","B4","P4","B5","S1_r","R2","S2","R5","S4","B9","P6","B8","R4","B7","P5","B6","S3","R3"]
    # layers = ["S1_full","S3_full","S4_full"]
    # gates = gates + layers

    soup = BeautifulSoup(svg_content, "xml")
    # for image in soup.find_all("image"):
    #     image.decompose()
    paths = soup.find_all("path", attrs={"inkscape:label": True})

    for path in paths:
        gate = path.get("inkscape:label")
        if gate not in gate_colors:
            continue

        value = gate_colors[gate]

        # Handle both object and simple value formats
        if isinstance(value, dict):
            color_value = value.get("value")
            opacity = value.get("opacity", fill_opacity)
        else:
            color_value = value
            opacity = fill_opacity

        # Convert value to color
        if isinstance(color_value, (int, float)):
            color = sm.to_rgba(color_value)
            hex_color = mcolors.to_hex(color)
        elif isinstance(color_value, str):
            hex_color = color_value
        else:
            raise ValueError(
                f"Invalid color value for gate {gate}: {color_value}. Must be float (0-1) or hex color string."
            )

        path["style"] = (
            f"stroke:#000000;stroke-width:0.264583;stroke-opacity:0.1;fill:{hex_color};fill-opacity:{opacity}"
        )

    with open(svg_target, "w") as file:
        output = str(soup)
        file.write(output)

    # Export PNG if requested
    if export_png:
        png_path = svg_target.with_suffix('.png')
        
        inkscape_args = [
            'inkscape',
            '--export-type=png',
            '--export-background-opacity=0',
        ]
        
        # Add size arguments if specified
        if png_size:
            width, height = png_size
            inkscape_args.extend([
                f'--export-width={width}',
                f'--export-height={height}',
            ])
            
        inkscape_args.extend([
            '--export-filename=' + str(png_path),
            str(svg_target)
        ])
        
        try:
            result = subprocess.run(
                inkscape_args,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"PNG exported to {png_path}")
            return str(svg_target), str(png_path)
        except subprocess.CalledProcessError as e:
            print(f"Error exporting PNG: {e.stderr}")
            return str(svg_target), None
    
    return str(svg_target), None


def colorbar_helper(sm):
    import matplotlib as mpl

    mpl.rcParams["axes.linewidth"] = 0.5  # set the value globally
    plt.rcParams["xtick.major.size"] = 2
    plt.rcParams["xtick.major.width"] = 0.5
    plt.rcParams["ytick.major.size"] = 2
    plt.rcParams["ytick.major.width"] = 0.5
    plt.rcParams["xtick.major.pad"] = 4.5
    plt.rcParams["ytick.major.pad"] = 4.5
    plt.rcParams["text.antialiased"] = True
    plt.rcParams["lines.antialiased"] = True
    plt.rcParams.update({"font.size": 6, "font.family": "Times New Roman"})

    w, h = 0.66, 4.4375
    true_height = 2
    fig = plt.figure(figsize=(true_height * w / h, true_height * h / h))
    ax = fig.add_subplot()

    # ax.set_facecolor((1.0, 1.0, 1.0, 0.0))
    # ax = fig.add_subplot()
    # fig.tight_layout()
    plt.colorbar(
        sm,
        cax=ax,
    )
    # ax.set_facecolor((1.0, 1.0, 1.0, 0.0))
    ax.patch.set_alpha(0.00)
    fig.tight_layout()
    fig.savefig("voltages_colored_colorbar.svg", dpi=8 * 96, transparent=True)
    plt.show()

