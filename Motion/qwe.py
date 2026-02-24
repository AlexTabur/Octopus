import dearpygui.dearpygui as dpg
import math

dpg.create_context()
dpg.create_viewport()
dpg.setup_dearpygui()

size = 8
q_left  = -size/2
q_right = size/2
q_bot   = -size/2
q_top   = size/2
q_front = size/2
q_back  = -size/2

verticies = [
    [q_left,  q_top,  q_front],   # 0
    [q_right, q_top,  q_front],   # 1       4     5
    [q_right, q_bot,  q_front],   # 2    0     1
    [q_left,  q_bot,  q_front],   # 3       7     6
    [q_left,  q_top,  q_back],    # 4    3     2
    [q_right, q_top,  q_back],    # 5
    [q_right, q_bot,  q_back],    # 6
    [q_left,  q_bot,  q_back],    # 7
]

top_verticies = [
    [0,  q_top,  0],    # 0
    [0,  q_top,  0],    # 1
    [0,  q_top,  0],    # 2
    [0,  q_top,  0]     # 3
]

front_verticies = [
    [0,  0,  q_front],   # 0
    [0,  0,  q_front],   # 1
    [0,  0,  q_front],   # 2
    [0,  0,  q_front]    # 3
]

left_verticies = [
    [q_right,  0,  0],   # 0
    [q_right,  0,  0],   # 1
    [q_right,  0,  0],   # 2
    [q_right,  0,  0],   # 3
]

color = [250, 200, 150, 100]

width = 500
height= 500
center = [(width / 2)-20, height / 2]
radius = 160

def place(x,y,z):
    # X
    top_verticies[0][0] = q_left + x
    top_verticies[1][0] = q_left + x
    top_verticies[2][0] = q_left + x + 1
    top_verticies[3][0] = q_left + x + 1
    front_verticies[0][0] = q_left + x
    front_verticies[1][0] = q_left + x + 1
    front_verticies[2][0] = q_left + x + 1
    front_verticies[3][0] = q_left + x
    # Y
    front_verticies[0][1] = q_bot + y + 1
    front_verticies[1][1] = q_bot + y + 1
    front_verticies[2][1] = q_bot + y
    front_verticies[3][1] = q_bot + y
    left_verticies[0][1] = q_bot + y + 1
    left_verticies[1][1] = q_bot + y + 1
    left_verticies[2][1] = q_bot + y
    left_verticies[3][1] = q_bot + y
    # Z
    top_verticies[0][2] = q_front - z
    top_verticies[1][2] = q_front - z - 1
    top_verticies[2][2] = q_front - z - 1
    top_verticies[3][2] = q_front - z
    left_verticies[0][2] = q_front - z - 1
    left_verticies[1][2] = q_front - z
    left_verticies[2][2] = q_front - z
    left_verticies[3][2] = q_front - z - 1

    dpg.configure_item("top_pos", p1=top_verticies[0], p2=top_verticies[1], p3=top_verticies[2], p4=top_verticies[3])
    dpg.configure_item("front_pos", p1=front_verticies[0], p2=front_verticies[1], p3=front_verticies[2], p4=front_verticies[3])
    dpg.configure_item("left_pos", p1=left_verticies[0], p2=left_verticies[1], p3=left_verticies[2], p4=left_verticies[3])

def rotate(x_rot, y_rot, z_rot):

    view = dpg.create_fps_matrix([1, 0, 50], 0.0, 0.0)
    proj = dpg.create_perspective_matrix(math.pi * 45.0 / 180.0, 1.0, 0.1, 100)
    model = dpg.create_rotation_matrix(math.pi * x_rot / 180.0, [1, 0, 0]) * \
            dpg.create_rotation_matrix(math.pi * y_rot / 180.0, [0, 1, 0]) * \
            dpg.create_rotation_matrix(math.pi * z_rot / 180.0, [0, 0, 1])
    dpg.apply_transform("cube", proj*view*model)

with dpg.window(label="tutorial", width=550, height=550):

    with dpg.drawlist(width=width, height=height, tag="d_list"):

        with dpg.draw_layer(tag="main pass", depth_clipping=False, perspective_divide=True, cull_mode=dpg.mvCullMode_Back):
            with dpg.draw_node(tag="cube"):
                dpg.draw_quad(verticies[0], verticies[1], verticies[2], verticies[3], color=[255, 255, 255])#, fill=colors[1])  # front
                dpg.draw_quad(verticies[0], verticies[4], verticies[5], verticies[1], color=[255, 255, 255])#, fill=colors[2])  # top
                dpg.draw_quad(verticies[1], verticies[5], verticies[6], verticies[2], color=[255, 255, 255])#, fill=colors[3])  # right

                dpg.draw_quad(top_verticies[0], top_verticies[1], top_verticies[2], top_verticies[3],
                              thickness=0.01, color=color, fill=color, tag="top_pos")
                dpg.draw_quad(front_verticies[0], front_verticies[1], front_verticies[2], front_verticies[3],
                              thickness=0.01, color=color, fill=color, tag="front_pos")
                dpg.draw_quad(left_verticies[0], left_verticies[1], left_verticies[2], left_verticies[3],
                              thickness=0.01, color=color, fill=color, tag="left_pos")

                place(1,4,3)

x_rot = 15
y_rot = -28
z_rot = 0

dpg.set_clip_space("main pass", 0, 0, 500, 500, -1.0, 1.0)
rotate(x_rot, y_rot, z_rot)

dpg.show_viewport()
x = 1
y = 4
z = 3
i=0
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()
    i+=1
    if i>100:
        i=0
        x+=1
        y+=1
        z+=1
        if x>=8: x=0
        if y>=8: y=0
        if z>=8: z=0
        place(x,y,z)

dpg.destroy_context()