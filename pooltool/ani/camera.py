#! /usr/bin/env python

from panda3d.core import TransparencyAttrib

from pooltool.ani.globals import Global, require_showbase


class PlayerCam:
    @require_showbase
    def init(self):
        self.node = Global.base.camera
        self.lens = Global.base.camLens
        self.lens.setNear(0.02)

        self.states = {}
        self.last_state = None
        self.has_focus = False

    def create_focus(self, parent=None, pos=None):
        if parent is None:
            parent = Global.base.render

        self.focus = parent.attachNewNode("camera_focus")
        self.focus.setH(-90)

        # create visible object
        self.focus_object = Global.loader.loadModel("smiley.egg")
        self.focus_object.setScale(0.005)
        self.focus_object.setTransparency(TransparencyAttrib.MAlpha)
        self.focus_object.setAlphaScale(0.4)
        self.focus_object.setH(-90)  # Smiley faces away from camera ways
        self.focus.setR(
            -10
        )  # Move 'head' up so you're not staring at the butt of the cue
        self.focus_object.setColor(1, 0, 0, 1)
        self.focus_object.reparentTo(self.focus)

        if pos is not None:
            self.focus.setPos(*pos)

        self.node.reparentTo(self.focus)
        self.node.setPos(2, 0, 0)
        self.node.lookAt(self.focus)

        self.has_focus = True

    def update_focus(self, pos):
        self.focus.setPos(pos)

    def scale_focus(self):
        """Scale the camera's focus object

        The focus marker is a small dot to show where the camera is centered, and where
        it rotates about. This helps a lot in navigating the camera effectively. Here
        the marker is scaled so that it is always a constant size, regardless of how
        zoomed in or out the camera is.
        """
        # `dist` is the distance from the camera to the focus object and is equivalent
        # to: cam_pos, focus_pos = player_cam.node.getPos(render),
        # player_cam.focus_object.getPos(render) dist = (cam_pos -
        # focus_pos).length()
        dist = self.node.getX()
        self.focus_object.setScale(0.002 * dist)

    def get_state(self):
        return {
            "CamHpr": self.node.getHpr(),
            "CamPos": self.node.getPos(),
            "FocusHpr": self.focus.getHpr() if self.has_focus else None,
            "FocusPos": self.focus.getPos() if self.has_focus else None,
        }

    def store_state(self, name, overwrite=False):
        if name in self.states:
            if overwrite:
                self.remove_state(name)
            else:
                raise Exception(f"PlayerCam :: '{name}' is already a camera state")

        self.states[name] = self.get_state()
        self.last_state = name

    def load_state(self, name, ok_if_not_exists=False):
        if name not in self.states:
            if ok_if_not_exists:
                return
            else:
                raise Exception(f"PlayerCam :: '{name}' is not a camera state")

        self.node.setPos(self.states[name]["CamPos"])
        self.node.setHpr(self.states[name]["CamHpr"])

        if self.has_focus:
            self.focus.setPos(self.states[name]["FocusPos"])
            self.focus.setHpr(self.states[name]["FocusHpr"])

    def load_last(self, ok_if_not_exists=False):
        """Loads the last state that was stored"""
        self.load_state(self.last_state, ok_if_not_exists=ok_if_not_exists)

    def remove_state(self, name):
        del self.states[name]

    def has_state(self, name):
        return True if name in self.states else False


player_cam = PlayerCam()
