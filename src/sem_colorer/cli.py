import argparse
import json
from pathlib import Path
from sem_colorer.core import (
    svg_gate_colorer,
    get_svg_gates,
    generate_color_spec_from_npz,
)


def generate_color_template(svg_path: str, output_path: str):
    """Generate a template colors.json file for the gates in an SVG."""
    gates = get_svg_gates(svg_path)

    template = {
        "colormap": "viridis",
        "norm_range": [0, 1],
        "gate_colors": {gate: {"value": 0.5, "opacity": 0.7} for gate in gates},
    }

    with open(output_path, "w") as f:
        json.dump(template, f, indent=4)
    print(f"Generated template at {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Color SVG files based on specifications"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Color command
    color_parser = subparsers.add_parser("color", help="Color an SVG file")
    color_parser.add_argument("svg_origin", type=str, help="Path to source SVG file")
    color_parser.add_argument(
        "--output", "-o", type=str, help="Path for colored SVG output"
    )
    color_parser.add_argument(
        "--spec", "-s", type=str, help="Path to JSON color specification file"
    )
    color_parser.add_argument(
        "--opacity", "-a", type=float, default=0.5, help="Default fill opacity"
    )
    color_parser.add_argument(
        "--png", "-p", action="store_true", help="Also export as PNG"
    )
    color_parser.add_argument("--width", "-w", type=int, help="PNG width in pixels")
    color_parser.add_argument("--height", "-t", type=int, help="PNG height in pixels")

    # Template command
    template_parser = subparsers.add_parser(
        "template", help="Generate a template colors.json"
    )
    template_parser.add_argument("svg_file", type=str, help="Path to source SVG file")
    template_parser.add_argument(
        "--output", "-o", type=str, help="Output path for colors.json"
    )

    # NPZ command (new)
    npz_parser = subparsers.add_parser("npz", help="Generate colors.json from NPZ file")
    npz_parser.add_argument("npz_file", type=str, help="Path to NPZ file with voltages")
    npz_parser.add_argument("svg_file", type=str, help="Path to SVG file")
    npz_parser.add_argument(
        "--output", "-o", type=str, help="Output path for colors.json"
    )
    npz_parser.add_argument(
        "--colormap", "-c", type=str, default="viridis", help="Matplotlib colormap name"
    )
    npz_parser.add_argument("--min", type=float, help="Normalization minimum")
    npz_parser.add_argument("--max", type=float, help="Normalization maximum")
    npz_parser.add_argument(
        "--opacity", "-a", type=float, default=0.7, help="Default opacity"
    )

    args = parser.parse_args()

    try:
        if args.command == "color":
            png_size = None
            if args.width and args.height:
                png_size = (args.width, args.height)
            elif args.width or args.height:
                print(
                    "Warning: Both width and height must be specified for custom PNG size"
                )

            svg_path, png_path = svg_gate_colorer(
                svg_origin=args.svg_origin,
                svg_target=args.output,
                color_spec=args.spec,
                fill_opacity=args.opacity,
                export_png=args.png,
                png_size=png_size,
            )
            print(f"SVG saved to: {svg_path}")
            if png_path:
                print(f"PNG saved to: {png_path}")
        elif args.command == "template":
            output_path = args.output or Path(args.svg_file).with_name("colors.json")
            generate_color_template(args.svg_file, output_path)
        elif args.command == "npz":
            norm_range = (
                (args.min, args.max)
                if args.min is not None and args.max is not None
                else (0, 1)
            )
            spec = generate_color_spec_from_npz(
                args.npz_file, args.svg_file, args.colormap, norm_range, args.opacity
            )
            output_path = args.output or Path(args.svg_file).with_name("colors.json")
            with open(output_path, "w") as f:
                json.dump(spec, f, indent=4)
            print(f"Generated color specification at {output_path}")
        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    main()

