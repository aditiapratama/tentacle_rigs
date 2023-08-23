bl_info = {
    "name": "Tentacle Rig",
    "author": "Clément Foucault",
    "version": (1, 0),
    "blender": (2, 7, 6),
    "location": "View3D > Edit Armature > Tools",
    "description": "Convert a bone to a tantacule rig",
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

def select_edit_bone(bone_name):
    bpy.ops.object.select_pattern(pattern=bone_name, extend=False)
    return bpy.context.selected_editable_bones[0]

def select_pose_bone(bone_name):
    bpy.ops.object.select_pattern(pattern=bone_name, extend=False)
    return bpy.context.selected_pose_bones[0]

def select_object(obj_name):
    bpy.ops.object.select_pattern(pattern=obj_name, extend=False)
    return bpy.context.selected_objects[0]

def parent_object(child,target):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_pattern(pattern=child.name, extend=False)
    bpy.ops.object.select_pattern(pattern=target.name, extend=True)
    bpy.context.scene.objects.active = target;
    bpy.ops.object.parent_set(type='OBJECT',keep_transform=False)

def add_HLP_sphere():
    #Helper shape
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=1, fill_type='NOTHING', view_align=False,)
    helper = bpy.context.active_object
    helper.name = "HLP_sphere"
    rot = radians(-90)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.resize( value=(.25,.25,.25) )
    bpy.ops.mesh.duplicate()
    bpy.ops.transform.rotate( value=(rot), axis=(0,1,0), release_confirm=False )
    bpy.ops.mesh.duplicate()
    bpy.ops.transform.rotate( value=(rot), axis=(0,0,1), release_confirm=False )
    bpy.ops.object.mode_set(mode='OBJECT')
    helper.layers = [n == 19 for n in range(0, 20)] 
    
def add_spline(num_control,context,head,tail):

    #Adding and formating spline
    bpy.ops.curve.primitive_nurbs_path_add(location = head)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.de_select_first()
    bpy.ops.curve.de_select_last()
    bpy.ops.curve.delete(type='VERT')

    v1 = bpy.context.selected_objects[0].data.splines[0].points[0].co.copy().resized(3)
    v2 = bpy.context.selected_objects[0].data.splines[0].points[1].co.copy().resized(3)

    v1.negate()
    v2 = tail - v2

    bpy.ops.curve.de_select_first()
    bpy.ops.transform.translate(value=(v1.x,v1.y,v1.z))
    bpy.ops.curve.de_select_first()

    bpy.ops.curve.de_select_last()
    bpy.ops.transform.translate(value=(v2.x,v2.y,v2.z))

    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.subdivide(number_cuts=(num_control-2))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    curve = bpy.context.selected_objects[0]
    curve.name = "tentacle_curve"
    spline = curve.data.splines[0]
    spline.order_u = 3

    return curve

def add_driver_variable(driver,TRig,rot_axe,bone_target):

    var = driver.variables.new()
    var.type = 'TRANSFORMS'
    targ = var.targets[0]
    targ.id = TRig
    targ.bone_target = bone_target
    targ.transform_type = 'ROT_'+rot_axe
    targ.transform_space = 'LOCAL_SPACE'

def setup_ctrl_bones(c_bone,ctrl_indep):

    bpy.ops.object.mode_set(mode='POSE')
    c_bone.bone.show_wire = True
    c_bone.custom_shape = bpy.context.scene.objects['HLP_sphere']
    
    bpy.ops.object.mode_set(mode='EDIT')
    c_edit_bone = select_edit_bone(c_bone.name)
    c_edit_bone.use_connect = False
    c_edit_bone.use_deform = False
    if ctrl_indep :
        c_edit_bone.parent = None

def setup_def_bones(def_bone,i,TRig,TRig_EXP,seg_bone,basename):

    bpy.ops.object.mode_set(mode='POSE')
    
    def_bone.bone.use_inherit_scale = False
    def_bone.bone.bbone_segments = seg_bone
    def_bone.rotation_mode = 'XYZ'

    ik_bone_name = 'IK_'+basename+'_tent.' + str(i).zfill(3)
    exp_bone_name = 'EXP_'+basename+'_tent.' + str(i).zfill(3)

    #Add constraints to bone
    TRig.data.bones.active = TRig.data.bones[def_bone.name]
    
    bpy.ops.pose.constraint_add(type='COPY_SCALE')
    constr = def_bone.constraints["Copy Scale"] #SplineIK rotConstr
    constr.name = "SplineIK"
    constr.target = TRig_EXP
    constr.subtarget = ik_bone_name

    bpy.ops.pose.constraint_add(type='COPY_LOCATION')
    constr = def_bone.constraints["Copy Location"] #Expr rotConstr
    constr.name = "ExprChain"
    constr.target = TRig_EXP
    constr.subtarget = ik_bone_name

    #Add driver to rotations
    
    #Add Drivers Rotation X
    fcurve = def_bone.driver_add("rotation_euler",0)
    driver = fcurve.driver
    driver.type = 'SUM'
    add_driver_variable(driver, TRig_EXP, "X", ik_bone_name)
    add_driver_variable(driver, TRig_EXP, "X", exp_bone_name)

    #Add Drivers Rotation Y
    fcurve = def_bone.driver_add("rotation_euler",1)
    driver = fcurve.driver
    driver.type = 'SUM'
    add_driver_variable(driver, TRig_EXP, "Y", ik_bone_name)
    add_driver_variable(driver, TRig_EXP, "Y", exp_bone_name)

    #Add Drivers Rotation Z
    fcurve = def_bone.driver_add("rotation_euler",2)
    driver = fcurve.driver
    driver.type = 'SUM'
    add_driver_variable(driver, TRig_EXP, "Z", ik_bone_name)
    add_driver_variable(driver, TRig_EXP, "Z", exp_bone_name)

def add_driver_single_prop_variable(driver,name,TRig,ctrl_bone_name):

    var = driver.variables.new()
    var.name = name
    var.type = "SINGLE_PROP"
    targ = var.targets[0]
    targ.id = TRig
    targ.data_path = 'pose.bones["'+ctrl_bone_name+'"]["'+name+'"]'

def driver_exp(driver,prefix,frequence,phase,offset,amp_start,amp_end,amp_start_offset,TRig,i,num_subdiv,ctrl_bone_name):

    time = "bpy.context.scene.frame_current"

    fre = prefix+frequence
    pha = prefix+phase
    off = prefix+offset
    ast = prefix+amp_start
    aen = prefix+amp_end
    aso = prefix+amp_start_offset

    driver.type = 'SCRIPTED'
    driver.expression = 'radians(sin('+time+'*'+fre+'+'+pha+'+'+off+'*('+str(i)+'-1)/('+str(num_subdiv)+'-1))*(' \
                                +ast+'*('+str(i)+'-'+aso+'+abs('+str(i)+'-'+aso+'))/(2*(' \
                                +str(num_subdiv)+'-'+aso+'))+'+aen+'*(1.0-('+str(i)+'/'+str(num_subdiv)+'))))'

    #Add variables
    add_driver_single_prop_variable(driver, fre, TRig, ctrl_bone_name)
    add_driver_single_prop_variable(driver, pha, TRig, ctrl_bone_name)
    add_driver_single_prop_variable(driver, off, TRig, ctrl_bone_name)
    add_driver_single_prop_variable(driver, ast, TRig, ctrl_bone_name)
    add_driver_single_prop_variable(driver, aen, TRig, ctrl_bone_name)
    add_driver_single_prop_variable(driver, aso, TRig, ctrl_bone_name)

    #Add variables to the ctrl bone
    ctrl_pose_bone = TRig.pose.bones[ctrl_bone_name]

    #Add custom properties to 1st controller
    ctrl_pose_bone[off] = 30
    ctrl_pose_bone[fre] = 0.1
    ctrl_pose_bone[pha] = 1.0
    ctrl_pose_bone[ast] = 50.0
    ctrl_pose_bone[aen] = 0
    ctrl_pose_bone[aso] = 1.0


def setup_exp_bones(bone,i,num_subdiv,TRig,basename):
    ctrl_bone_name = 'CTRL_'+basename+'_tent.001'
    
    bone.rotation_mode = 'XYZ'
    bone.bone.use_deform = False
    bone.bone.show_wire = True
    
    #Add Drivers Rotation X
    fcurve = bone.driver_add("rotation_euler",0)
    driver = fcurve.driver
    driver_exp(driver,'X_','frequence','phase','offset','amp_start','amp_end','amp_start_offset',TRig,i,num_subdiv,ctrl_bone_name)
    
    #Add Drivers Rotation Z
    fcurve = bone.driver_add("rotation_euler",2)
    driver = fcurve.driver
    driver_exp(driver,'Z_','frequence','phase','offset','amp_start','amp_end','amp_start_offset',TRig,i,num_subdiv,ctrl_bone_name)
    
def separate_bone(rig,bone_name):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.objects.active = rig;
    bpy.ops.object.mode_set(mode='EDIT')

    list_before = [ob for ob in bpy.data.objects if ob.type == 'ARMATURE']
    bpy.ops.object.select_pattern(pattern=bone_name, extend=False)
    bpy.ops.armature.separate()
    list_after = [ob for ob in bpy.data.objects if ob.type == 'ARMATURE']

    for i in list_before:
        list_after.remove(i)

    new_armature = list_after[0]
    new_armature.animation_data_clear()

    return new_armature
    
def merge_armature(armature,destination_name):

    bpy.ops.object.mode_set(mode='OBJECT')

    if destination_name in bpy.context.scene.objects:
        bpy.ops.object.select_pattern(pattern=destination_name, extend=False)
        bpy.ops.object.select_pattern(pattern=armature.name, extend=True)
        bpy.context.scene.objects.active = bpy.context.scene.objects[destination_name];

        bpy.ops.object.join();

        armature = bpy.context.scene.objects[destination_name];
    else:
        armature.name = destination_name

    bpy.context.scene.objects.active = armature;

    return armature

def subdivide_bone(prefix,num_subdiv,armature,basename):

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.objects.active = armature;
    bpy.ops.object.mode_set(mode='EDIT')

    bone_name = prefix+"_"+basename+"_"

    bpy.ops.object.select_pattern(pattern=bone_name, extend=False)
    edit_bone = bpy.context.selected_editable_bones[0]
    edit_bone.tail = (edit_bone.tail + ((edit_bone.tail - edit_bone.head)/(num_subdiv-1)) )
    bpy.ops.armature.subdivide(number_cuts=(num_subdiv-1))

    #Renaming works only in pose Mode
    bpy.ops.object.mode_set(mode='POSE')
    i = 1
    edit_bone = armature.pose.bones[bone_name]
    edit_bone.name = bone_name+"tent.001"

    while edit_bone.children :
        i += 1
        edit_bone = edit_bone.children[0]
        edit_bone.name = bone_name+"tent." + str(i).zfill(3)

    bpy.ops.object.mode_set(mode='EDIT')

    return armature.pose.bones[bone_name+"tent.001"]

def setup_spline(basename,head,tail,num_control,TRig_CTRL,context):
    #Add Curve
    curve = add_spline(num_control,context,head,tail)
    curve.name = basename+"_tent_curve"

    #Spline HOOKS
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.objects.active = curve
    bpy.ops.object.mode_set(mode='EDIT')
    
    i = 0
    for point in curve.data.splines[0].points :
        i += 1
        bpy.ops.curve.select_all(action='DESELECT')
        bpy.ops.object.modifier_add(type='HOOK')
        modifier = curve.modifiers["Hook"]
        modifier.name = "TentacleHook." + str(i).zfill(3)
        modifier.object = TRig_CTRL
        modifier.subtarget = "CTRL_"+basename+"_tent." + str(i).zfill(3)
        point.select = True
        bpy.ops.object.hook_assign(modifier=modifier.name)
        bpy.ops.object.hook_recenter(modifier=modifier.name)
        bpy.ops.object.hook_reset(modifier=modifier.name)

    return curve

def bone_to_tentacle(self,context,bone):

    self.TRig = bpy.context.active_object

    basename = bone.name

    #Create root bones
    bone = select_edit_bone(basename)
    #basename += "_"+str(chr(int(time.time() % 35 ))) TODO  find hsh function
    bone.name = "DEF_"+basename+"_"

    #Get Head & Tail coords
    head = bone.head + self.TRig.location
    tail = bone.tail - bone.head

    #Check if hlp_sphere exists
    if 'HLP_sphere' not in bpy.context.scene.objects :
        add_HLP_sphere()

    #Unhide all Objects (TODO only desired armatures)
    for obj in bpy.data.objects:
        obj.hide = False


    # --------- Duplicate Bone ----------- #

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.objects.active = self.TRig
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.armature.duplicate()
    bone = bpy.context.selected_editable_bones[0]
    bone.name = "EXP_"+basename+"_"

    bpy.ops.armature.duplicate()
    bone = bpy.context.selected_editable_bones[0]
    bone.name = "IK_"+basename+"_"

    bpy.ops.armature.duplicate()
    bone = bpy.context.selected_editable_bones[0]
    bone.name = "CTRL_"+basename+"_"



    # --------- Setup CTRL ----------- #

    c_bone = select_edit_bone("CTRL_"+basename+"_")
    self.TRig_CTRL = separate_bone(self.TRig, c_bone.name)
    self.TRig_CTRL = merge_armature(self.TRig_CTRL, self.TRig.name+"_CTRL")

    #Subdivide CTRL
    c_bone = subdivide_bone("CTRL", self.num_control, self.TRig_CTRL, basename)
    c_bone["ystretch"] = True
    setup_ctrl_bones(c_bone, self.ctrl_indep)

    while c_bone.children :
        c_bone = c_bone.children[0]
        setup_ctrl_bones(c_bone, self.ctrl_indep)



    # --------- Setup Spline ----------- #

    curve = setup_spline(basename,head,tail,self.num_control,self.TRig_CTRL,context)



    # ---- Separation IK and EXP ----- #

    self.TRig_EXP = separate_bone(self.TRig, "IK_"+basename+"_")
    self.TRig_EXP = merge_armature(self.TRig_EXP, self.TRig.name+"_EXP")

    self.TRig_EXP = separate_bone(self.TRig, "EXP_"+basename+"_")
    self.TRig_EXP = merge_armature(self.TRig_EXP, self.TRig.name+"_EXP")



    # --------- Setup IK ----------- #

    i_bone = subdivide_bone("IK", self.num_subdiv, self.TRig_EXP, basename)

    #for the 1st bone apply the Orient constraint
    bpy.ops.object.mode_set(mode='POSE')
    self.TRig_EXP.data.bones.active = self.TRig_EXP.data.bones[i_bone.name]
    bpy.ops.pose.constraint_add(type='COPY_ROTATION')
    constr = i_bone.constraints[0]
    constr.target = self.TRig_CTRL
    constr.subtarget = "CTRL_"+basename+"_tent.001"

    bpy.ops.object.mode_set(mode='EDIT')
    while i_bone.children :
        i_bone = i_bone.children[0]
        i_bone.bone.use_deform = False
        i_bone.bone.show_wire = True

    #for the last bone apply the constraint
    bpy.ops.object.mode_set(mode='POSE')
    self.TRig_EXP.data.bones.active = self.TRig_EXP.data.bones[i_bone.name]
    bpy.ops.pose.constraint_add(type='SPLINE_IK')
    constr = i_bone.constraints[0]
    constr.chain_count = self.num_subdiv
    constr.target = curve

    fcurve = constr.driver_add("use_y_stretch")
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = 'bool(ystretch)'

    #Driver to switch stretch
    add_driver_single_prop_variable(driver, "ystretch", self.TRig_CTRL, 'CTRL_'+basename+'_tent.001')




    # --------- Setup EXP ----------- #

    e_bone = subdivide_bone("EXP", self.num_subdiv, self.TRig_EXP, basename)

    i = 1
    setup_exp_bones(e_bone,i,self.num_subdiv,self.TRig_CTRL,basename)

    while e_bone.children :
        i += 1
        e_bone = e_bone.children[0]
        setup_exp_bones(e_bone,i,self.num_subdiv,self.TRig_CTRL,basename)



    # --------- Setup DEF ----------- #

    d_bone = subdivide_bone("DEF", self.num_subdiv, self.TRig, basename)
    
    i = 1
    setup_def_bones(d_bone, i, self.TRig, self.TRig_EXP, self.seg_bone, basename)

    while d_bone.children :
        i += 1
        d_bone = d_bone.children[0] 
        setup_def_bones(d_bone, i, self.TRig, self.TRig_EXP, self.seg_bone, basename)



    # --------- Cleaning ----------- #

    parent_object(curve, self.TRig_CTRL)
    bpy.ops.object.select_pattern(pattern='*_tent_curve', extend=False)
    for curve in bpy.context.selected_objects:
        curve.hide = True
    self.TRig_EXP.hide = True

    #Changing back to CTRL Rig
    bpy.context.scene.objects.active = self.TRig
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.armature.select_all(action='DESELECT')



def multi_tentacle(self,context):
    selected_bones_before = [b.name for b in context.selected_editable_bones]
    for bone_name in selected_bones_before:
        bone = select_edit_bone(bone_name)
        bone_to_tentacle(self,context,bone)

#Convert to Tentacle
class TR_convert_bone_to_tentacle(Operator):
    bl_idname = "armature.convert_to_tentacle"
    bl_label = "Convert to tentacle"
    bl_description = "Convert selected bone to Tentacle Rig"
    bl_options = {'MACRO'}

    num_subdiv = IntProperty(
                name="Number of bones",
                description="Number of bones in the tentacle chain",
                min=2, max=99,
                default=5,
                )

    num_control = IntProperty(
                name="Number of control",
                description="Number of control bone for the spline",
                min=3, max=99,
                default=4,
                )

    seg_bone = IntProperty(
                name="Segment per bone",
                description="Number of segment for curved bones",
                min=1, max=32,
                default=1,
                )

    ctrl_indep = BoolProperty(
                name="Independant controls",
                description="Check for parenting controls bones into an FK chain",
                default=False,
                )

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_ARMATURE' :
            return bool(len(context.selected_editable_bones))
        else :
            return False

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        multi_tentacle(self,context)
        return {'FINISHED'}


#Add Parent In CTRL RIG

def create_ctrl_parent(self,context,bone):
    #Save selected bones
    selected_bones_before = [b.name for b in context.selected_editable_bones if b.name != bone.name]

    self.TRig = bpy.context.active_object

    basename = bone.name

    bpy.ops.armature.duplicate()
    bone = bpy.context.selected_editable_bones[0]
    bone.name = "CTRL_"+basename

    self.TRig_CTRL = separate_bone(self.TRig, bone.name)
    self.TRig_CTRL = merge_armature(self.TRig_CTRL, self.TRig.name+"_CTRL")

    #Changing to CTRL Rig
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.objects.active = self.TRig
    bpy.ops.object.mode_set(mode='POSE')

    self.TRig.data.bones.active = self.TRig.data.bones[basename]
        
    bone = select_pose_bone(basename)

    bpy.ops.pose.constraint_add(type='COPY_TRANSFORMS')
    constr = bone.constraints["Copy Transforms"]
    constr.name = "Controler Transformation"
    constr.target = self.TRig_CTRL
    constr.subtarget = "CTRL_"+basename

    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.armature.select_all(action='DESELECT')
    for bone_name in selected_bones_before:
        bpy.ops.object.select_pattern(pattern=bone_name, extend=True)

def multi_ctrl_parent(self,context):
    selected_bones_before = [b.name for b in context.selected_editable_bones]
    for bone_name in selected_bones_before:
        bone = select_edit_bone(bone_name)
        create_ctrl_parent(self,context,bone)


class TR_add_bone_to_ctrl_rig(Operator):
    bl_idname = "armature.create_ctrl_parent"
    bl_label = "Bone to CTRL Rig"
    bl_description = "Bone to CTRL Rig"
    bl_options = {'MACRO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_ARMATURE' :
            return bool(len(context.selected_editable_bones))
        else :
            return False

    def execute(self, context):
        multi_ctrl_parent(self,context)
        return {'FINISHED'}

# Registration

#Convert selected bones option
class TR_convert_bone_to_tentacle_button_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "armature_edit"
    bl_label = "Tentacle Rig"
    bl_category = "Tools"
    def draw(self, context):
        self.layout.operator("armature.convert_to_tentacle", text="Convert to tentacle", icon='BONE_DATA')
        self.layout.operator("armature.create_ctrl_parent", text="Bone to CTRL Rig", icon='CONSTRAINT')

def register():
    bpy.utils.register_class(TR_convert_bone_to_tentacle)
    bpy.utils.register_class(TR_add_bone_to_ctrl_rig)
    bpy.utils.register_class(TR_convert_bone_to_tentacle_button_panel)


def unregister():
    bpy.utils.unregister_class(TR_convert_bone_to_tentacle)
    bpy.utils.unregister_class(TR_add_bone_to_ctrl_rig)
    bpy.utils.unregister_class(TR_convert_bone_to_tentacle_button_panel)



if __name__ == "__main__":
    register()