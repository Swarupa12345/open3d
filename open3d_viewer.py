#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Open3D viewer for the DRDL aerospace GUI. Python 3.8 compatible."""
from __future__ import print_function
import argparse
import ctypes
import json
import os
import sys
import time
from datetime import datetime

import numpy as np
import open3d as o3d

try:
    import aero_body_vis
except Exception as exc:
    raise RuntimeError("Could not import aero_body_vis.py from the project folder: {}".format(exc))


COLORS = {
    "nose": [0.78, 0.84, 0.91],
    "body": [0.58, 0.66, 0.76],
    "wing": [0.12, 0.48, 0.88],
    "tail": [0.91, 0.30, 0.25],
}


def _surface_to_mesh(surface, color):
    """Triangulate a rectangular X/Y/Z surface grid into an Open3D mesh."""
    X, Y, Z = [np.asarray(v, dtype=float) for v in surface]
    if X.shape != Y.shape or X.shape != Z.shape or X.ndim != 2:
        raise ValueError("Expected matching 2-D surface grids; got {}, {}, {}".format(
            X.shape, Y.shape, Z.shape))
    rows, cols = X.shape
    if rows < 2 or cols < 2:
        raise ValueError("Surface grid must be at least 2 x 2")
    vertices = np.column_stack((X.ravel(), Y.ravel(), Z.ravel()))
    triangles = []
    for i in range(rows - 1):
        base = i * cols
        next_base = (i + 1) * cols
        for j in range(cols - 1):
            a = base + j
            b = a + 1
            c = next_base + j
            d = c + 1
            triangles.append((a, c, b))
            triangles.append((b, c, d))
    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(vertices)
    mesh.triangles = o3d.utility.Vector3iVector(np.asarray(triangles, dtype=np.int32))
    mesh.compute_vertex_normals()
    mesh.paint_uniform_color(color)
    return mesh


def build_aircraft_meshes(gui_params):
    """Use the project's existing geometry builder and GUI-to-visualizer adapter."""
    fixed = {
        "nose_diameter": 250.0,
        "body_diameter": 250.0,
        "nose_bluntness": 0.15,
        "tail_sweep": 40.0,
        "w_hinge_line": 0.7,
        "f_hinge_line": 0.75,
        "tail_config": "cruciform",
    }
    key_map = {
        "nose_len": "nose_length", "body_len": "body_length",
        "wing_le": "wing_le", "root_chord": "root_chord",
        "tip_chord": "tip_chord", "semi_span": "semi_span",
        "root_th": "root_th", "tip_th": "tip_th",
        "wing_sweep": "wing_sweep", "tail_le": "tail_le",
        "root_chord1": "tail_root_chord", "tip_chord1": "tail_tip_chord",
        "semi_span1": "tail_semi_span", "root_th1": "tail_root_th",
        "tip_th1": "tail_tip_th",
    }
    vis_params = dict(fixed)
    for gui_key, vis_key in key_map.items():
        if gui_key in gui_params:
            vis_params[vis_key] = float(gui_params[gui_key])

    geometry, _hinges, _normalized_params = aero_body_vis.build_geometry(vis_params)
    meshes = []
    meshes.append(_surface_to_mesh(geometry["nose"], COLORS["nose"]))
    meshes.append(_surface_to_mesh(geometry["body"], COLORS["body"]))
    for part_name, surfaces in geometry["wings_tails"].items():
        color = COLORS["wing"] if "wing" in part_name else COLORS["tail"]
        for surface in surfaces:
            meshes.append(_surface_to_mesh(surface, color))
    return meshes


def _read_params(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _export_meshes(meshes, extension, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, "aircraft_{}.{}".format(stamp, extension))
    combined = o3d.geometry.TriangleMesh()
    for mesh in meshes:
        combined += mesh
    combined.compute_vertex_normals()
    if extension.lower() == "stl":
        ok = o3d.io.write_triangle_mesh(path, combined, write_ascii=False)
    else:
        ok = o3d.io.write_triangle_mesh(path, combined, write_ascii=False,
                                        write_vertex_normals=True)
    if not ok:
        print("ERROR: Open3D could not write {}".format(path), flush=True)
    else:
        print("Exported: {}".format(path), flush=True)
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--params-file", required=True)
    parser.add_argument("--title", default="DRDL Aircraft", help="Viewer window title")
    parser.add_argument("--watch", action="store_true",
                        help="reload geometry when the GUI updates the parameter file")
    args = parser.parse_args()

    params_path = os.path.abspath(args.params_file)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    export_dir = os.path.join(project_dir, "open3d_exports")
    params = _read_params(params_path)
    meshes = build_aircraft_meshes(params)
    vis = o3d.visualization.VisualizerWithKeyCallback()
    base_title = "{} | S: Export STL | O: Export OBJ | Esc: Close".format(args.title)
    current_title = [base_title]
    if not vis.create_window(window_name=base_title, width=1280, height=800, visible=True):
        raise RuntimeError("Open3D could not create its viewer window.")
    for mesh in meshes:
        vis.add_geometry(mesh, reset_bounding_box=False)
    render_option = vis.get_render_option()
    render_option.background_color = np.asarray([0.035, 0.055, 0.085])
    render_option.mesh_show_back_face = True
    render_option.light_on = True
    try:
        vis.get_view_control().set_zoom(0.72)
    except Exception:
        pass

    def export_stl(_visualizer):
        _export_meshes(meshes, "stl", export_dir)
        return False

    def export_obj(_visualizer):
        _export_meshes(meshes, "obj", export_dir)
        return False

    vis.register_key_callback(ord("S"), export_stl)
    vis.register_key_callback(ord("O"), export_obj)

    last_mtime = os.path.getmtime(params_path) if os.path.exists(params_path) else 0
    last_check = 0.0
    last_generation = params.get("_generation")

    def update_generation_title(generation):
        """Show GEN n in the native Open3D window title on Windows."""
        if generation is None:
            return
        try:
            label = "GEN {}".format(int(generation))
        except (TypeError, ValueError):
            return
        new_title = "{} | {} | S: Export STL | O: Export OBJ | Esc: Close".format(
            args.title, label)
        if new_title == current_title[0]:
            return
        if os.name == "nt":
            try:
                hwnd = ctypes.windll.user32.FindWindowW(None, current_title[0])
                if hwnd:
                    ctypes.windll.user32.SetWindowTextW(hwnd, new_title)
                    current_title[0] = new_title
            except Exception:
                pass

    update_generation_title(last_generation)
    try:
        while vis.poll_events():
            now = time.time()
            if args.watch and now - last_check > 0.25:
                last_check = now
                try:
                    mtime = os.path.getmtime(params_path)
                    if mtime != last_mtime:
                        updated_params = _read_params(params_path)
                        new_meshes = build_aircraft_meshes(updated_params)
                        generation = updated_params.get("_generation")
                        if generation is not None and generation != last_generation:
                            update_generation_title(generation)
                            last_generation = generation
                        for old_mesh in meshes:
                            vis.remove_geometry(old_mesh, reset_bounding_box=False)
                        meshes[:] = new_meshes
                        for new_mesh in meshes:
                            vis.add_geometry(new_mesh, reset_bounding_box=False)
                        last_mtime = mtime
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    print("Geometry refresh skipped: {}".format(exc), flush=True)
            vis.update_renderer()
            time.sleep(0.01)
    finally:
        vis.destroy_window()


if __name__ == "__main__":
    main()
