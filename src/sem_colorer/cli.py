import argparse
from pathlib import Path
from sem_colorer.core import svg_gate_colorer

def main():
    parser = argparse.ArgumentParser(description='Color SVG files based on specifications')
    parser.add_argument('svg_origin', type=str, help='Path to source SVG file')
    parser.add_argument('--output', '-o', type=str, help='Path for colored SVG output')
    parser.add_argument('--spec', '-s', type=str, help='Path to JSON color specification file')
    parser.add_argument('--opacity', '-a', type=float, default=0.5, help='Default fill opacity')

    args = parser.parse_args()

    try:
        svg_gate_colorer(
            svg_origin=args.svg_origin,
            svg_target=args.output,
            color_spec=args.spec,
            fill_opacity=args.opacity
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == '__main__':
    main()