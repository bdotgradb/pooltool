#! /usr/bin/env python

import numpy as np

import pooltool.ani as ani
import pooltool.ani.tasks as tasks
import pooltool.ani.utils as autils
from pooltool.ani.action import Action
from pooltool.ani.camera import player_cam
from pooltool.ani.globals import Global
from pooltool.ani.hud import HUDElement, hud
from pooltool.ani.modes.datatypes import BaseMode, Mode
from pooltool.ani.mouse import mouse
from pooltool.objects.ball import Ball
from pooltool.objects.cue import cue_avoid


class ViewMode(BaseMode):
    name = Mode.view
    keymap = {
        Action.aim: False,
        Action.call_shot: False,
        Action.fine_control: False,
        Action.move: False,
        Action.stroke: False,
        Action.quit: False,
        Action.zoom: False,
        Action.cam_save: False,
        Action.cam_load: False,
        Action.show_help: False,
        Action.pick_ball: False,
        Action.ball_in_hand: False,
        Action.power: False,
        Action.elevation: False,
        Action.english: False,
        Action.prev_shot: False,
        Action.introspect: False,
        Action.hide_cue: False,
        Action.exec_shot: False,
    }

    def __init__(self):
        super().__init__()

        # In this state, the cue sticks to the cue_avoid.min_theta
        self.magnet_theta = True
        # if cue angle is within this many degrees from cue_avoid.min_theta, it sticks
        # to cue_avoid.min_theta
        self.magnet_threshold = 0.2

    def enter(self, move_active=False, load_prev_cam=False):
        mouse.hide()
        mouse.relative()
        mouse.track()

        if Global.shots.active is not None:
            Global.shots.active.cue.hide_nodes(ignore=("cue_cseg",))

        if load_prev_cam:
            player_cam.load_state(Mode.view)

        player_cam.scale_focus()

        if move_active:
            self.keymap[Action.move] = True

        self.register_keymap_event("escape", Action.quit, True)
        self.register_keymap_event("mouse1", Action.zoom, True)
        self.register_keymap_event("mouse1-up", Action.zoom, False)
        self.register_keymap_event("a", Action.aim, True)
        self.register_keymap_event("s", Action.stroke, True)
        self.register_keymap_event("v", Action.move, True)
        self.register_keymap_event("v-up", Action.move, False)
        self.register_keymap_event("1", Action.cam_save, True)
        self.register_keymap_event("2", Action.cam_load, True)
        self.register_keymap_event("h", Action.show_help, True)
        self.register_keymap_event("q", Action.pick_ball, True)
        self.register_keymap_event("g", Action.ball_in_hand, True)
        self.register_keymap_event("c", Action.call_shot, True)
        self.register_keymap_event("i", Action.introspect, True)
        self.register_keymap_event("i-up", Action.introspect, False)
        self.register_keymap_event("b", Action.elevation, True)
        self.register_keymap_event("b-up", Action.hide_cue, True)
        self.register_keymap_event("e", Action.english, True)
        self.register_keymap_event("e-up", Action.hide_cue, True)
        self.register_keymap_event("x", Action.power, True)
        self.register_keymap_event("x-up", Action.hide_cue, True)
        self.register_keymap_event("p-up", Action.prev_shot, True)
        self.register_keymap_event("space", Action.exec_shot, True)
        self.register_keymap_event("space-up", Action.exec_shot, False)

        tasks.add(self.view_task, "view_task")
        tasks.add(self.shared_task, "shared_task")
        if ani.settings["gameplay"]["cue_collision"]:
            tasks.add(cue_avoid.collision_task, "collision_task")

    def exit(self):
        tasks.remove("view_task")
        tasks.remove("shared_task")

        if ani.settings["gameplay"]["cue_collision"]:
            tasks.remove("collision_task")
        player_cam.store_state(Mode.view, overwrite=True)

    def view_task(self, task):
        if self.keymap[Action.stroke]:
            Global.mode_mgr.change_mode(Mode.stroke)
        elif self.keymap[Action.pick_ball]:
            Global.mode_mgr.change_mode(Mode.pick_ball)
        elif self.keymap[Action.call_shot]:
            Global.mode_mgr.change_mode(Mode.call_shot)
        elif self.keymap[Action.ball_in_hand]:
            Global.mode_mgr.change_mode(Mode.ball_in_hand)
        elif self.keymap[Action.zoom]:
            self.zoom_camera_view()
        elif self.keymap[Action.move]:
            self.move_camera_view()
        elif self.keymap[Action.hide_cue]:
            self.keymap[Action.hide_cue] = False
            self.keymap[Action.english] = False
            self.keymap[Action.elevation] = False
            self.keymap[Action.power] = False
            if Global.shots.active is not None:
                Global.shots.active.cue.hide_nodes(ignore=("cue_cseg",))
        elif self.keymap[Action.elevation]:
            self.view_elevate_cue()
        elif self.keymap[Action.english]:
            self.view_apply_english()
        elif self.keymap[Action.power]:
            self.view_apply_power()
        elif self.keymap[Action.aim]:
            Global.mode_mgr.change_mode(Mode.aim, enter_kwargs=dict(load_prev_cam=True))
        elif self.keymap[Action.exec_shot]:
            Global.mode_mgr.mode_stroked_from = Mode.view
            Global.shots.active.cue.set_object_state_as_render_state(skip_V0=True)
            Global.shots.active.cue.strike()
            Global.mode_mgr.change_mode(Mode.calculate)
        elif self.keymap[Action.prev_shot]:
            self.keymap[Action.prev_shot] = False
            if len(Global.shots) > 1:
                self.change_animation(Global.shots.active_index - 1)
                Global.mode_mgr.change_mode(
                    Mode.shot, enter_kwargs=dict(init_animations=False)
                )
                return task.done
        else:
            self.rotate_camera_view()

        return task.cont

    def zoom_camera_view(self):
        with mouse:
            s = -mouse.get_dy() * ani.zoom_sensitivity

        player_cam.node.setPos(autils.multiply_cw(player_cam.node.getPos(), 1 - s))
        player_cam.scale_focus()

    def move_camera_view(self):
        with mouse:
            dxp, dyp = mouse.get_dx(), mouse.get_dy()

        # NOTE This conversion _may_ depend on how I initialized player_cam.focus
        h = player_cam.focus.getH() * np.pi / 180 + np.pi / 2
        dx = dxp * np.cos(h) - dyp * np.sin(h)
        dy = dxp * np.sin(h) + dyp * np.cos(h)

        player_cam.focus.setX(player_cam.focus.getX() + dx * ani.move_sensitivity)
        player_cam.focus.setY(player_cam.focus.getY() + dy * ani.move_sensitivity)

    def rotate_camera_view(self):
        if self.keymap[Action.fine_control]:
            fx, fy = ani.rotate_fine_sensitivity_x, ani.rotate_fine_sensitivity_y
        else:
            fx, fy = ani.rotate_sensitivity_x, ani.rotate_sensitivity_y

        with mouse:
            alpha_x = player_cam.focus.getH() - fx * mouse.get_dx()
            alpha_y = max(min(0, player_cam.focus.getR() + fy * mouse.get_dy()), -90)

        player_cam.focus.setH(alpha_x)  # Move view laterally
        player_cam.focus.setR(alpha_y)  # Move view vertically

    def view_apply_power(self):
        Global.shots.active.cue.show_nodes(ignore=("cue_cseg",))

        with mouse:
            dy = mouse.get_dy()

        min_V0, max_V0 = (
            hud.elements[HUDElement.power].min_strike,
            hud.elements[HUDElement.power].max_strike,
        )

        V0 = Global.shots.active.cue.V0 + dy * ani.power_sensitivity
        if V0 < min_V0:
            V0 = min_V0
        if V0 > max_V0:
            V0 = max_V0

        Global.shots.active.cue.set_state(V0=V0)
        hud.elements[HUDElement.power].set(V0)

    def view_elevate_cue(self):
        Global.shots.active.cue.show_nodes(ignore=("cue_cseg",))

        cue = Global.shots.active.cue.get_node("cue_stick_focus")

        with mouse:
            delta_elevation = mouse.get_dy() * ani.elevate_sensitivity

        old_elevation = -cue.getR()
        new_elevation = max(0, min(ani.max_elevate, old_elevation + delta_elevation))

        if cue_avoid.min_theta >= new_elevation - self.magnet_threshold:
            # user set theta to minimum value, resume cushion tracking
            self.magnet_theta = True
            new_elevation = cue_avoid.min_theta
        else:
            # theta has been modified by the user, so no longer tracks the cushion
            self.magnet_theta = False

        cue.setR(-new_elevation)

        Global.shots.active.cue.set_state(theta=new_elevation)
        hud.elements[HUDElement.jack].set(new_elevation)

    def view_apply_english(self):
        Global.shots.active.cue.show_nodes(ignore=("cue_cseg",))

        with mouse:
            dx, dy = mouse.get_dx(), mouse.get_dy()

        cue = Global.shots.active.cue.get_node("cue_stick")
        cue_focus = Global.shots.active.cue.get_node("cue_stick_focus")
        R = Global.shots.active.cue.follow.R

        delta_y, delta_z = dx * ani.english_sensitivity, dy * ani.english_sensitivity

        # y corresponds to side spin, z to top/bottom spin
        new_y = cue.getY() + delta_y
        new_z = cue.getZ() + delta_z

        norm = np.sqrt(new_y**2 + new_z**2)
        if norm > ani.max_english * R:
            new_y *= ani.max_english * R / norm
            new_z *= ani.max_english * R / norm

        cue.setY(new_y)
        cue.setZ(new_z)

        # if application of english increases min_theta beyond current elevation,
        # increase elevation
        if (
            self.magnet_theta
            or cue_avoid.min_theta >= -cue_focus.getR() - self.magnet_threshold
        ):
            cue_focus.setR(-cue_avoid.min_theta)

        a, b, theta = (
            -new_y / R,
            new_z / R,
            -Global.shots.active.cue.get_node("cue_stick_focus").getR(),
        )
        Global.shots.active.cue.set_state(a=a, b=b, theta=theta)
        hud.elements[HUDElement.english].set(a, b)
        hud.elements[HUDElement.jack].set(theta)

    def change_animation(self, shot_index):
        # Switch shots
        Global.shots.clear_animation()
        Global.shots.active.teardown()
        Global.shots.set_active(shot_index)
        Global.shots.active.buildup()

        # Initialize the animation
        Global.shots.set_animation()
        Global.shots.loop_animation()

        # A lot of dumb things to make the cue track the initial position of the ball
        dummy = Ball("dummy")
        dummy.R = Global.shots.active.cue.cueing_ball.R
        dummy.rvw = Global.shots.active.cue.cueing_ball.history.rvw[0]
        dummy.render()
        Global.shots.active.cue.init_focus(dummy)
        Global.shots.active.cue.set_render_state_as_object_state()
        Global.shots.active.cue.follow = None
        dummy.remove_nodes()
        del dummy

        cue_avoid.init_collisions()

        # Set the HUD
        hud.elements.get(HUDElement.english).set(
            Global.shots.active.cue.a, Global.shots.active.cue.b
        )
        hud.elements.get(HUDElement.jack).set(Global.shots.active.cue.theta)
        hud.elements.get(HUDElement.power).set(Global.shots.active.cue.V0)
