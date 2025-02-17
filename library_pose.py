

import bpy
import json
import os
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy.types import Operator, Panel


class DeleteBonePose(Operator, ImportHelper):
    bl_idname = "delete.bone_pose"
    bl_label = "Delete Bone Pose"
    filename_ext = ".png"  # Menerima file PNG untuk dipilih

    def execute(self, context):
        # Path gambar yang dipilih
        image_path = self.filepath
        image_name = os.path.splitext(os.path.basename(image_path))[0]  # Nama file tanpa ekstensi

        # Mengambil folder dari path gambar
        selected_folder = os.path.dirname(image_path)
        data_pose_folder = os.path.join(selected_folder, "data_pose")  # Menentukan folder data_pose
        script_path = os.path.join(data_pose_folder, f"{image_name}.py")  # Menentukan path skrip yang sesuai

        # Cek apakah folder data_pose ada
        if os.path.exists(data_pose_folder):
            # Hapus file skrip jika ada
            if os.path.exists(script_path):
                try:
                    os.remove(script_path)
                    self.report({'INFO'}, f"Deleted script: {script_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to delete script: {str(e)}")
            else:
                self.report({'WARNING'}, f"No matching script found for image: {image_name}")

            # Hapus file gambar jika ada
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    self.report({'INFO'}, f"Deleted image: {image_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to delete image: {str(e)}")
            else:
                self.report({'WARNING'}, f"No matching image found: {image_path}")
        else:
            self.report({'WARNING'}, f"No 'data_pose' folder found in: {selected_folder}")

        return {'FINISHED'}


#===================================================================================================    

def flip_selected_pose(context):
    """Flip the pose for selected bones"""
    try:
        bpy.ops.pose.copy()  # Copy selected pose
        bpy.ops.pose.paste(flipped=True)  # Paste flipped pose
    except RuntimeError:
        context.report({'WARNING'}, "Flip Pose failed. Ensure you're in Pose Mode and bones are selected.")


def serialize_custom_properties(bone):
    custom_props = {}
    for prop_name in bone.keys():
        if prop_name == "rigify_parameters":  # Skip rigify_parameters
            continue

        value = bone[prop_name]

        # Skip Blender internal object references
        if isinstance(value, bpy.types.ID) or "<bpy id prop" in str(value):
            continue

        if isinstance(value, (int, float, str)):
            custom_props[prop_name] = value

    return custom_props if custom_props else None  # Return None if empty


class ExportBonePose(Operator, ExportHelper):
    bl_idname = "export.bone_pose"
    bl_label = "Export Bone Pose"
    filename_ext = ".py"

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'ARMATURE':
            self.report({'WARNING'}, "Select an armature in pose mode.")
            return {'CANCELLED'}

        bones = context.selected_pose_bones
        if not bones:
            self.report({'WARNING'}, "No bones selected.")
            return {'CANCELLED'}

        bone_data = {}

        for bone in bones:
            custom_props = serialize_custom_properties(bone)
            bone_info = {
                "location": list(bone.location),
                "rotation_quaternion": list(bone.rotation_quaternion),
                "rotation_euler": list(bone.rotation_euler),
                "scale": list(bone.scale)
            }
            if custom_props:  # Only add if there are custom properties
                bone_info["custom_properties"] = custom_props

            bone_data[bone.name] = bone_info

        selected_folder = os.path.dirname(self.filepath)
        script_filename = os.path.basename(self.filepath)
        script_name = os.path.splitext(script_filename)[0]  # Get file name without extension
        
        data_pose_folder = os.path.join(selected_folder, "data_pose")
        if not os.path.exists(data_pose_folder):
            os.makedirs(data_pose_folder)
        
        script_path = os.path.join(data_pose_folder, script_filename)
        image_path = os.path.join(selected_folder, f"{script_name}.png")

        script_content = f"""
import bpy
import json

def apply_bone_pose():
    obj = bpy.context.object
    if obj is None or obj.type != 'ARMATURE':
        print("No armature selected.")
        return

    bone_data = {json.dumps(bone_data, indent=4)}
    selected_bones = [bone.name for bone in bpy.context.selected_pose_bones]
    matched_bones = {{}}

    for bone_name, data in bone_data.items():
        if bone_name in selected_bones:
            matched_bones[bone_name] = data

    if not matched_bones:
        print("No matching bones found.")
        return

    for bone_name, data in matched_bones.items():
        bone = obj.pose.bones.get(bone_name)
        if bone:
            bone.location = data["location"]
            bone.rotation_quaternion = data["rotation_quaternion"]
            bone.rotation_euler = data["rotation_euler"]
            bone.scale = data["scale"]
            if "custom_properties" in data:
                for prop, value in data["custom_properties"].items():
                    bone[prop] = value

apply_bone_pose()
"""
        script_content = script_content.replace("true", "True").replace("false", "False")

        with open(script_path, 'w') as file:
            file.write(script_content)

        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = image_path
        bpy.ops.render.view_show()
        bpy.ops.render.opengl(write_still=True)

        self.report({'INFO'}, f"Bone pose exported as script: {script_path} and image: {image_path}")

        return {'FINISHED'}





class ImportBonePose(Operator, ImportHelper):
    bl_idname = "import.bone_pose"
    bl_label = "Import Bone Pose"
    filename_ext = "*.png"

    def execute(self, context):
        selected_image_path = self.filepath
        script_name = os.path.splitext(os.path.basename(selected_image_path))[0] + ".py"
        script_path = os.path.join(os.path.dirname(selected_image_path), "data_pose", script_name)

        if os.path.exists(script_path):
            with open(script_path, "r") as file:
                exec(file.read(), globals())
            self.report({'INFO'}, f"Executed script: {script_path}")
        else:
            self.report({'WARNING'}, f"No matching script found: {script_path}")
            return {'CANCELLED'}
        # **Tambahkan keyframe jika opsi set_keyframes dicentang**
        if context.scene.set_keyframes:
            self.insert_keyframes(context)
            self.report({'INFO'}, "Keyframes inserted after importing pose.")
            
        return {'FINISHED'}
    
    

    def insert_keyframes(self, context):
        obj = context.object
        if obj and obj.type == 'ARMATURE':
            current_frame = context.scene.frame_current
            for bone in context.selected_pose_bones:
                # Insert keyframes for the selected bones
                bpy.context.view_layer.objects.active = obj  # Set active object
                bpy.ops.anim.keyframe_insert_by_name(type="LocRotScaleCProp")

    def apply_bone_pose(self):
        obj = bpy.context.object
        if obj is None or obj.type != 'ARMATURE':
            print("No armature selected.")
            return

        bone_data = {json.dumps(bone_data, indent=4)}
        selected_bones = [bone.name for bone in bpy.context.selected_pose_bones]
        matched_bones = {}

        for bone_name, data in bone_data.items():
            if bone_name in selected_bones:
                matched_bones[bone_name] = data

        if not matched_bones:
            print("No matching bones found.")
            return

        for bone_name, data in matched_bones.items():
            bone = obj.pose.bones.get(bone_name)
            if bone:
                # Hindari mengganti rigify_parameters dan properti khusus lainnya
                if 'rigify_parameters' not in data['custom_properties']:
                    bone.location = data["location"]
                    bone.rotation_quaternion = data["rotation_quaternion"]
                    bone.rotation_euler = data["rotation_euler"]
                    bone.scale = data["scale"]
                    for prop, value in data["custom_properties"].items():
                        if prop != 'bbdObject':  # Menghindari mengganti properti ID
                            bone[prop] = value
                else:
                    print(f"Skipping 'rigify_parameters' for bone: {bone_name}")


        return {'FINISHED'}

    def insert_keyframes(self, context):
        obj = context.object
        if obj and obj.type == 'ARMATURE':
                # Tentukan frame yang akan diberi keyframe
                current_frame = context.scene.frame_current
                
                # Simpan referensi ke objek aktif untuk menghindari memanggilnya berulang kali
                bpy.context.view_layer.objects.active = obj

                # Menggunakan batching untuk menambahkan keyframe secara kolektif
                selected_bones = context.selected_pose_bones
                
                if selected_bones:
                        # Aktifkan animasi hanya sekali
                        bpy.ops.anim.keyframe_insert(type="LocRotScaleCProp")
                        
                        # Setelah itu, set keyframe untuk setiap bone
                        for bone in selected_bones:
                                # Bisa ditambahkan properti tertentu jika diperlukan, misalnya:
                                # bone.keyframe_insert(data_path="location")
                                # bone.keyframe_insert(data_path="rotation_euler")
                                # bone.keyframe_insert(data_path="scale")
                                pass  # Proses insert keyframe sudah terhandle oleh keyframe_insert sebelumnya
                else:
                        self.report({'WARNING'}, "No bones selected.")
                        


#======== Value slider ===================================================================

class ApplyPercentageOperator(bpy.types.Operator):
    bl_idname = "pose.apply_percentage"
    bl_label = "Apply Percentage to Bones"
    
    def execute(self, context):
        armature = context.object
        
        # Pastikan objek adalah armature
        if armature.type != 'ARMATURE':
            self.report({'WARNING'}, "Selected object is not an armature")
            return {'CANCELLED'}
        
        percentage = context.scene.percentage_value / 100  # Konversi persentase menjadi rasio
        calc_location = context.scene.calc_location
        calc_rotation = context.scene.calc_rotation
        calc_scale = context.scene.calc_scale
        calc_custom_property = context.scene.calc_custom_property
        
        # Iterasi setiap bone yang terseleksi
        for bone in armature.pose.bones:
            if bone.bone.select:
                # Kalkulasi dan modifikasi data asli bone (bukan data objek)
                
                if calc_location:
                    # Lokasi bone (transformasi relatif)
                    bone.location.x *= percentage
                    bone.location.y *= percentage
                    bone.location.z *= percentage

                if calc_rotation:
                    # Rotasi bone (Euler)
                    bone.rotation_euler.x *= percentage
                    bone.rotation_euler.y *= percentage
                    bone.rotation_euler.z *= percentage

                    # Rotasi bone (Quaternion)
                    bone.rotation_quaternion.x *= percentage
                    bone.rotation_quaternion.y *= percentage
                    bone.rotation_quaternion.z *= percentage
                    bone.rotation_quaternion.w *= percentage

                if calc_scale:
                    # Skala bone
                    bone.scale.x *= percentage
                    bone.scale.y *= percentage
                    bone.scale.z *= percentage

                if calc_custom_property:
                    # Kalkulasi custom property jika ada
                    for prop_name in bone.keys():
                        if prop_name != "_RNA_UI":  # Menghindari modifikasi metadata internal
                            current_value = bone[prop_name]
                            bone[prop_name] = current_value * percentage
        
        # Set keyframe sesuai dengan kategori yang dipilih
        bpy.ops.anim.keyframe_insert_by_name(type="LocRotScaleCProp")
        
        return {'FINISHED'}
#========================================================================================    
class OBJECT_OT_FlipPoseOperator(bpy.types.Operator):
    """Flip the current pose"""
    bl_idname = "object.flip_pose"
    bl_label = "Flip Pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'ARMATURE' or obj.mode != 'POSE':
            self.report({'WARNING'}, "Flip Pose failed. Ensure an armature is selected and you're in Pose Mode.")
            return {'CANCELLED'}
        
        flip_selected_pose(context)
        return {'FINISHED'}
#    ==========================================================

    
class Raha_tombol_panel_POSE_LIB(bpy.types.Panel):
    bl_label = "Bone Pose Export/Import"
    bl_idname = "PT_BonePose"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 10

    def draw(self, context):
        layout = self.layout
        layout.label(text="Export & Import Bone Pose")


        row = layout.row()
        row.operator("export.bone_pose", text="Export Pose")
        row.operator("import.bone_pose", text="Import Pose")
        layout.operator("delete.bone_pose", text="Delete Pose")
        layout.prop(context.scene, "set_keyframes", text="Set Keyframes")
       
        
        # Menambahkan panel Percentage

        row = layout.row()        
        row.prop(context.scene, "percentage_value", text="Percentage (%)")
        row.operator("pose.apply_percentage", text="Apply Percentage")         
        
        row = layout.row()
        # Checkbox untuk memilih apakah Location, Rotation, Scale, dan Custom Property yang ingin dihitung
        row.prop(context.scene, "calc_location", text="Location")
        row.prop(context.scene, "calc_rotation", text="Rotation")
        row.prop(context.scene, "calc_scale", text="Scale")
        row.prop(context.scene, "calc_custom_property", text="Custom Properties")
        # Tombol Apply
        layout.operator("object.flip_pose", text="Flip Pose")              
#=====================================================================================================        


def register():
    bpy.utils.register_class(ExportBonePose)
    bpy.utils.register_class(ImportBonePose)
    bpy.utils.register_class(OBJECT_OT_FlipPoseOperator)    
    bpy.utils.register_class(Raha_tombol_panel_POSE_LIB)
    bpy.utils.register_class(DeleteBonePose)

    
    bpy.utils.register_class(ApplyPercentageOperator)
    
    # Menambahkan properti untuk persen
    bpy.types.Scene.percentage_value = bpy.props.FloatProperty(name="Percentage", default=50)
    
    # Menambahkan properti untuk checkbox
    bpy.types.Scene.calc_location = bpy.props.BoolProperty(name="Location", default=True)
    bpy.types.Scene.calc_rotation = bpy.props.BoolProperty(name="Rotation", default=True)
    bpy.types.Scene.calc_scale = bpy.props.BoolProperty(name="Scale", default=True)
    bpy.types.Scene.calc_custom_property = bpy.props.BoolProperty(name="Custom Properties", default=True)    


    bpy.types.Scene.set_keyframes = BoolProperty(name="Set Keyframes")


def unregister():
    bpy.utils.unregister_class(ExportBonePose)
    bpy.utils.unregister_class(ImportBonePose)
    bpy.utils.unregister_class(OBJECT_OT_FlipPoseOperator)      
    bpy.utils.unregister_class(Raha_tombol_panel_POSE_LIB)
    bpy.utils.unregister_class(DeleteBonePose)

        
    del bpy.types.Scene.script_folder_path
    del bpy.types.Scene.set_keyframes
    bpy.utils.unregister_class(ApplyPercentageOperator)
    
    # Menghapus properti
    del bpy.types.Scene.percentage_value
    del bpy.types.Scene.calc_location
    del bpy.types.Scene.calc_rotation
    del bpy.types.Scene.calc_scale
    del bpy.types.Scene.calc_custom_property
    


if __name__ == "__main__":
    register()
