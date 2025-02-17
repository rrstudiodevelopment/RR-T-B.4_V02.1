

import bpy
import json
import mathutils


stored_matrices = {}

class RahaSaveBoneMatrix(bpy.types.Operator):
    """Menyimpan matrix location dan rotation dalam world space"""
    bl_idname = "object.save_bone_matrix"
    bl_label = "Simpan Matrix"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            bone = obj.pose.bones.get(context.active_pose_bone.name)
            if bone:
                stored_matrices[bone.name] = {
                    "matrix": [list(row) for row in (obj.matrix_world @ bone.matrix)]
                }
                self.report({'INFO'}, f"Matrix bone {bone.name} dalam world space disimpan.")
        else:
            self.report({'WARNING'}, "Harap masuk ke Pose Mode.")
        return {'FINISHED'}

class RahaApplyBoneMatrix(bpy.types.Operator):
    """Menerapkan matrix location dan rotation dalam world space serta membuat keyframe"""
    bl_idname = "object.apply_bone_matrix"
    bl_label = "Setel Matrix & Set Key"
    
    def execute(self, context):
        obj = context.object
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            bone = obj.pose.bones.get(context.active_pose_bone.name)
            if bone and bone.name in stored_matrices:
                matrix_data = stored_matrices[bone.name]["matrix"]
                bone.matrix = obj.matrix_world.inverted() @ mathutils.Matrix(matrix_data)
                bone.keyframe_insert(data_path="location", index=-1)
                bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
                bone.keyframe_insert(data_path="rotation_euler", index=-1)
                self.report({'INFO'}, f"Matrix bone {bone.name} diterapkan dalam world space dan keyframe diset.")
        else:
            self.report({'WARNING'}, "Harap masuk ke Pose Mode.")
        return {'FINISHED'}

class RahaForwardAnimation(bpy.types.Operator):
    """Menyimpan transformasi di frame awal lalu menerapkannya hingga frame akhir dengan keyframe"""
    bl_idname = "object.forward_animation"
    bl_label = "Forward"
    
    def execute(self, context):
        obj = context.object
        scene = context.scene
        start_frame = scene.start_frame
        end_frame = scene.end_frame
        
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            bone = obj.pose.bones.get(context.active_pose_bone.name)
            if bone:
                stored_matrices[bone.name] = {
                    "matrix": [list(row) for row in (obj.matrix_world @ bone.matrix)]
                }
                for frame in range(start_frame, end_frame + 1):
                    scene.frame_set(frame)
                    matrix_data = stored_matrices[bone.name]["matrix"]
                    bone.matrix = obj.matrix_world.inverted() @ mathutils.Matrix(matrix_data)
                    bone.keyframe_insert(data_path="location", index=-1)
                    bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
                    bone.keyframe_insert(data_path="rotation_euler", index=-1)
                self.report({'INFO'}, "Forward animation applied.")
        return {'FINISHED'}

class RahaBackwardAnimationBackwardAnimation(bpy.types.Operator):
    """Menyimpan transformasi di frame akhir lalu menerapkannya secara mundur hingga frame awal dengan keyframe"""
    bl_idname = "object.backward_animation"
    bl_label = "Backward"
    
    def execute(self, context):
        obj = context.object
        scene = context.scene
        start_frame = scene.start_frame
        end_frame = scene.end_frame
        
        if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
            bone = obj.pose.bones.get(context.active_pose_bone.name)
            if bone:
                scene.frame_set(end_frame)
                stored_matrices[bone.name] = {
                    "matrix": [list(row) for row in (obj.matrix_world @ bone.matrix)]
                }
                for frame in range(end_frame, start_frame - 1, -1):
                    scene.frame_set(frame)
                    matrix_data = stored_matrices[bone.name]["matrix"]
                    bone.matrix = obj.matrix_world.inverted() @ mathutils.Matrix(matrix_data)
                    bone.keyframe_insert(data_path="location", index=-1)
                    bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
                    bone.keyframe_insert(data_path="rotation_euler", index=-1)
                self.report({'INFO'}, "Backward animation applied.")
        return {'FINISHED'}

class RahaBoneMatrixPanel(bpy.types.Panel):
    """Panel untuk menyimpan dan menerapkan matrix bone dalam world space"""
    bl_label = "Fake constraint N step snap : raha tools"
    bl_idname = "OBJECT_PT_bone_matrix"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene       
        layout.label(text="Fake constraint")
        layout.operator("object.save_bone_matrix", text="Save data fake")
        layout.operator("object.apply_bone_matrix", text="Apply fake constraint")
        
        layout.separator()  
        layout.label(text="Step Snap")                      
        layout.prop(scene, "start_frame")
        layout.prop(scene, "end_frame")
        row = layout.row()
        row.operator("object.forward_animation", text="Forward", icon='TRIA_RIGHT')
        row.operator("object.backward_animation", text="Backward", icon='TRIA_LEFT')

classes = [RahaSaveBoneMatrix, RahaApplyBoneMatrix, RahaForwardAnimation, RahaBackwardAnimationBackwardAnimation, RahaBoneMatrixPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.start_frame = bpy.props.IntProperty(name="Start Frame", default=1)
    bpy.types.Scene.end_frame = bpy.props.IntProperty(name="End Frame", default=10)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.start_frame
    del bpy.types.Scene.end_frame

if __name__ == "__main__":
    register()
