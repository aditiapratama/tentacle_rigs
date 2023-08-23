bl_info = {
    "name": "Bone Shape Editor",
    "author": "Clément Foucault",
    "version": (1, 0),
    "blender": (2, 7, 6),
    "location": "View3D > Pose Armature > Tools",
    "description": "Create bone shape easily.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Rigging"}


import bpy
import time
from bpy.types import Operator, Menu, Panel
from bpy.props import IntProperty, BoolProperty, FloatVectorProperty 
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector
from math import *

def edit_bone_shape(self,context):
    bpy.ops.object.mode_set(mode='OBJECT')

    context.object.scale = Vector.Fill(3,self.size)

    bpy.ops.object.constraint_add(type='COPY_LOCATION')
    constr = context.object.constraints["Copy Location"]
    constr.name = "Edit Bone Shape Loc"
    constr.target = self.armature
    constr.subtarget = self.bname

    bpy.ops.object.constraint_add(type='COPY_ROTATION')
    constr = context.object.constraints["Copy Rotation"]
    constr.name = "Edit Bone Shape Rot"
    constr.target = self.armature
    constr.subtarget = self.bname

    self.bone.custom_shape = context.object
    self.bone.bone.show_wire = True

    try:
        context.object["BoneEdit"].active_armature = self.armature.name
    except:
        print("Property BoneEdit does not exists : Creating it")
    finally:
        context.object["BoneEdit"] = {}
        context.object["BoneEdit"]["active_armature"] = self.armature.name

    bpy.ops.object.mode_set(mode='EDIT')

def enter_edit_bone_shape(self,context):

    self.bone = context.selected_pose_bones[0];
    self.bname = self.bone.name
    self.armature = context.active_object
    self.size = (self.bone.tail - self.bone.head).length
    
    obj = self.bone.custom_shape
    # prev_layers = obj.layer.copy()

    obj.hide = False
    obj.hide_select = False
    # obj.layer = context.scene.layer

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_pattern(pattern=obj.name, extend=False)

    bpy.context.scene.objects.active = context.selected_objects[0]

    edit_bone_shape(self,context)

def create_edit_bone_shape(self,context):

    self.bone = context.selected_pose_bones[0];
    self.bname = self.bone.name
    self.armature = context.active_object
    self.size = (self.bone.tail - self.bone.head).length

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(radius=0.1/self.size, enter_editmode=True, location=(0.0, 0.0, 0.0))
    bpy.ops.mesh.primitive_cube_add(radius=0.1/self.size, location=(0.0, 1.0, 0.0))
    bpy.ops.object.mode_set(mode='OBJECT')

    context.object.name = "SHP_"+self.bname

    edit_bone_shape(self,context)

def exit_edit_bone_shape(self,context):
    bpy.ops.object.mode_set(mode='OBJECT')
    armature = ""
    obj = context.object

    try:
        armature = context.object["BoneEdit"]["active_armature"]
    except:
        print("Property BoneEdit does not exists")
    
    try:
        constraint = context.object.constraints["Edit Bone Shape Loc"]
        context.object.constraints.remove(constraint)
    except:
        print("No constraint to remove")
    finally:
        obj.hide = True
        obj.hide_render = True

        if armature != "":
            bpy.ops.object.select_pattern(pattern=armature, extend=False)
            bpy.context.scene.objects.active = context.selected_objects[0]
            bpy.ops.object.mode_set(mode='POSE')
    
def dupli_edit_bone_shape(self,context):
    self.bone = context.selected_pose_bones[0];
    self.bname = self.bone.name
    self.armature = context.active_object
    self.size = (self.bone.tail - self.bone.head).length

    obj = bpy.data.objects[self.armature.data.BoneEdit_selected_shape_object]

    print(obj.name)

    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_pattern(pattern=obj.name, extend=False)

    bpy.context.scene.objects.active = obj
    
    bpy.ops.object.duplicate()

    context.object.name = "SHP_"+self.bname

    #To not scale the desired shape
    context.object.scale = Vector.Fill(3,1/self.size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    edit_bone_shape(self,context)


class BoneEd_custom_shape_open(Operator):
    bl_idname = "armature.bone_edit_custom_shape_open"
    bl_label = ""
    bl_options = {'MACRO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'POSE' :
            return bool(len(context.selected_pose_bones))
        else :
            return False

    def execute(self, context):
        if context.selected_pose_bones[0].custom_shape != None:
            enter_edit_bone_shape(self,context)
        else :
            create_edit_bone_shape(self,context)
        return {'FINISHED'}

class BoneEd_custom_shape_apply(Operator):
    bl_idname = "armature.bone_edit_custom_shape_apply"
    bl_label = ""
    bl_options = {'MACRO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'POSE' :
            return bool(len(context.selected_pose_bones))
        else :
            return False

    def execute(self, context):
        if context.active_object.data.BoneEdit_selected_shape_object != None:
            dupli_edit_bone_shape(self,context)
        else:
            create_edit_bone_shape(self,context)
        return {'FINISHED'}

class BoneEd_custom_shape_create(Operator):
    bl_idname = "armature.bone_edit_custom_shape_create"
    bl_label = ""
    bl_options = {'MACRO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'POSE' :
            return bool(len(context.selected_pose_bones))
        else :
            return False

    def execute(self, context):
        create_edit_bone_shape(self,context)
        return {'FINISHED'}

class BoneEd_custom_shape_close(Operator):
    bl_idname = "armature.bone_edit_custom_shape_close"
    bl_label = ""
    bl_options = {'MACRO'}

    @classmethod
    def poll(cls, context):
        return True
        if context.mode == 'EDIT_ARMATURE' and context.object["BoneEdit"]:
            return context.object["BoneEdit"].active_armature
        else :
            return False

    def execute(self, context):
        exit_edit_bone_shape(self,context)
        return {'FINISHED'}

# PANEL

class BoneEd_custom_shape_open_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "posemode"
    bl_label = "Edit Bone Custom Shape"
    bl_category = "Tools"

    def draw(self, context):
        if context.selected_pose_bones[0].custom_shape != None:
            self.layout.operator("armature.bone_edit_custom_shape_open", text="Edit Curent Custom Shape" , icon='BONE_DATA')
            self.layout.prop_search(context.selected_pose_bones[0], "custom_shape", context.scene, "objects")
        else:
            if context.active_object.data.BoneEdit_selected_shape_object != "":
                self.layout.operator("armature.bone_edit_custom_shape_apply", text="Apply selected custom Shape" , icon='BONE_DATA')
            else:
                self.layout.operator("armature.bone_edit_custom_shape_create", text="Create custom Shape" , icon='BONE_DATA')
            self.layout.prop_search(context.object.data, "BoneEdit_selected_shape_object", context.scene, "objects")

class BoneEd_custom_shape_close_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_label = "Edit Bone Custom Shape"
    bl_category = "Tools"
    def draw(self, context):
        self.layout.operator("armature.bone_edit_custom_shape_close", text="Return to the previous Armature" , icon='BONE_DATA')


def register():
    bpy.utils.register_class(BoneEd_custom_shape_open)
    bpy.utils.register_class(BoneEd_custom_shape_create)
    bpy.utils.register_class(BoneEd_custom_shape_apply)
    bpy.utils.register_class(BoneEd_custom_shape_open_panel)
    bpy.utils.register_class(BoneEd_custom_shape_close)
    bpy.utils.register_class(BoneEd_custom_shape_close_panel)
    bpy.types.Armature.BoneEdit_selected_shape_object = bpy.props.StringProperty(name="Shape Object to apply")


def unregister():
    bpy.utils.unregister_class(BoneEd_custom_shape_open)
    bpy.utils.unregister_class(BoneEd_custom_shape_create)
    bpy.utils.unregister_class(BoneEd_custom_shape_apply)
    bpy.utils.unregister_class(BoneEd_custom_shape_open_panel)
    bpy.utils.unregister_class(BoneEd_custom_shape_close)
    bpy.utils.unregister_class(BoneEd_custom_shape_close_panel)
    del bpy.types.Armature.BoneEdit_selected_shape_object


if __name__ == "__main__":
    register()