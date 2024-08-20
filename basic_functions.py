import time
import bpy

import cProfile
import pstats
import io

class BasePanel(bpy.types.Panel):
    bl_label = "Default Panel"
    bl_idname = "SCENE_PT_BasePanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    def populate_ui(self, layout, property_group, item_rows):
            for item_row in item_rows:
                row = layout.row()
                if type(item_row) == list:
                    for item in item_row:
                        row.prop(property_group, item)
                elif type(item_row) == str:
                    if ';' in item_row:
                        text, icon = item_row.split(';')
                    else:
                        text, icon = item_row, '',
                    row.label(text=text, icon=icon)

    def draw(self, context):
        pass

def show_progress(ws, ref, progress, progress_text = ""):
    setattr(ref, 'progress', progress)
    setattr(ref, 'progress_text', progress_text)
    for screen in ws.screens:
        for area in screen.areas:
            area.tag_redraw()

def time_task(function, text = "", *args):
    start_time = time.perf_counter()
    res = function(*args)
    end_time = time.perf_counter()
    if (end_time - start_time) < 0.1:
        print(f'{text} - {(end_time - start_time):.4f}s')
    else:
        print(f'{text} - {(end_time - start_time):.2f}s')
    return res

def profiler(function, *args):
    pr = cProfile.Profile()
    pr.enable()

    res = function(*args)

    pr.disable()
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)

    ps.print_stats(lambda x: ps.stats[x][3] >= 10)
    print(s.getvalue())

    return res

def totuple(a):
    return tuple(map(tuple, a))