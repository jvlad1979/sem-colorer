import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
import json
from pathlib import Path
import matplotlib.colors as mcolors
from matplotlib.cm import ScalarMappable

# class SEM:
#     def __init__(self, gates : list[str], layers : list[str], gate_data_intensity : dict[str, float | tuple[float, float]]):
#         pass

# class SVGColorer:
#     def __init__(self, ):
#         pass

def load_color_spec(json_path):
    with open(json_path) as f:
        spec = json.load(f)
    return spec

def svg_gate_colorer(
    svg_origin: str | Path,
    svg_target: str | Path = None,
    color_spec: str | dict = None,
    fill_opacity: float = 0.5,
):
    """
    Color an SVG file based on specifications.
    
    Args:
        svg_origin: Path to source SVG file
        svg_target: Path for output SVG (if None, will append '_colored' to origin name)
        color_spec: Either path to JSON file or dict with color specifications
        fill_opacity: Default opacity for elements without specified opacity
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
    cmap = spec.get('colormap', 'viridis')
    norm_range = spec.get('norm_range', [0, 1])
    gate_colors = spec.get('gate_colors', {})
    
    # Create color mapper
    norm = Normalize(vmin=norm_range[0], vmax=norm_range[1])
    sm = ScalarMappable(cmap=cmap, norm=norm)
    with open(svg_origin) as file:
        svg_content = file.read()
    gates = ["R1","S1_l","B1","P1","B2","P2","B3","P3","B4","P4","B5","S1_r","R2","S2","R5","S4","B9","P6","B8","R4","B7","P5","B6","S3","R3"]
    layers = ["S1_full","S3_full","S4_full"]
    gates = gates + layers

    soup = BeautifulSoup(svg_content, "xml")

    paths = []

    for gate in gates:
        paths = paths + soup.find_all("path",attrs={"inkscape:label":gate})


    for i, path in enumerate(paths):
        gate = path.get('inkscape:label')
        if gate not in gate_colors:
            continue
            
        value = gate_colors[gate]
        
        # Handle both object and simple value formats
        if isinstance(value, dict):
            color_value = value.get('value')
            opacity = value.get('opacity', fill_opacity)
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
            raise ValueError(f"Invalid color value for gate {gate}: {color_value}. Must be float (0-1) or hex color string.")

        path["style"] = (f"stroke:#000000;stroke-width:0.264583;stroke-opacity:0.1;fill:{hex_color};fill-opacity:{opacity}")
    
    with open(svg_target, "w") as file:
        file.write(str(soup))

def colorbar_helper(sm):
    import matplotlib as mpl

    mpl.rcParams["axes.linewidth"] = 0.5  # set the value globally
    plt.rcParams["xtick.major.size"] = 2
    plt.rcParams["xtick.major.width"] = 0.5
    plt.rcParams["ytick.major.size"] = 2
    plt.rcParams["ytick.major.width"] = 0.5
    plt.rcParams["xtick.major.pad"] = 4.5
    plt.rcParams["ytick.major.pad"] = 4.5
    plt.rcParams['text.antialiased'] = True
    plt.rcParams['lines.antialiased'] = True
    plt.rcParams.update({"font.size": 6, "font.family": "Times New Roman"})


    w,h = .66,4.4375
    true_height = 2
    fig = plt.figure(figsize=(true_height*w/h, true_height*h/h))
    ax = fig.add_subplot()

    # ax.set_facecolor((1.0, 1.0, 1.0, 0.0))
    # ax = fig.add_subplot()
    # fig.tight_layout()
    plt.colorbar(sm, cax=ax,)
    # ax.set_facecolor((1.0, 1.0, 1.0, 0.0))
    ax.patch.set_alpha(0.00)
    fig.tight_layout()
    fig.savefig("voltages_colored_colorbar.svg", dpi=8*96,transparent=True)
    plt.show()