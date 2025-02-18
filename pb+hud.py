
import bpy
import os
import subprocess

#================================ HUD ============================================================
# Mengambil path ke direktori addon

# Dapatkan path addons dari Blender secara dinamis
ADDONS_PATH = bpy.utils.user_resource('SCRIPTS', path="addons")
SAFE_AREA_IMAGE_PATH = os.path.join(ADDONS_PATH, "Raha_Tools_LAUNCHER", "safe_area.png")



class RAHA_OT_ActivateHUD(bpy.types.Operator):
    """Operator to activate HUD settings"""
    bl_idname = "raha.activate_hud"
    bl_label = "Activate HUD"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')

        # Loop melalui semua objek di scene dan seleksi yang merupakan kamera
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                obj.select_set(True)

        # Set active object ke kamera pertama yang ditemukan (opsional)
        cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
        if cameras:
            bpy.context.view_layer.objects.active = cameras[0]
        scene = context.scene
        scene.render.use_stamp = True
        scene.render.use_stamp_note = True
        scene.render.use_stamp_camera = False
        scene.render.use_stamp_render_time = False
        scene.render.use_stamp_time = False 
        scene.render.use_stamp_filename = False               
        scene.render.use_stamp_lens = True
        scene.render.stamp_font_size = 32

        # Menyembunyikan elemen overlay
        area = next((area for area in bpy.context.screen.areas if area.type == 'VIEW_3D'), None)
        if area:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_bones = False
                    space.overlay.show_cursor = False
                    space.overlay.show_extras = False
                    space.overlay.show_motion_paths = False
                    space.overlay.show_relationship_lines = False

        # Menambahkan background image ke kamera
        camera = bpy.context.scene.camera
        if camera:
            if not camera.data.background_images:
                bg_image = camera.data.background_images.new()
            else:
                bg_image = camera.data.background_images[0]

            bg_image.image = bpy.data.images.load(SAFE_AREA_IMAGE_PATH)
            bg_image.show_background_image = True
            bg_image.display_depth = 'FRONT'  # Menetapkan display depth ke 'FRONT'

        # Menampilkan background image pada objek aktif
        obj = bpy.context.object
        if obj and obj.type == 'CAMERA':  
            obj.data.show_background_images = True
            if obj.data.background_images:
                obj.data.background_images[0].display_depth = 'FRONT'  # Pastikan display depth diatur ke 'FRONT'

        self.report({'INFO'}, "HUD activated with specified settings and overlays hidden")
        return {'FINISHED'}

class VIEW3D_OT_ToggleSafeArea(bpy.types.Operator):
    """Toggle the visibility of the safe area overlay"""
    bl_idname = "view3d.toggle_safe_area"
    bl_label = "Toggle Safe Area"

    def execute(self, context):
        camera = bpy.context.scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera found in the scene.")
            return {'CANCELLED'}

        if camera.data.background_images:
            bg_image = camera.data.background_images[0]
            bg_image.show_background_image = not bg_image.show_background_image

            status = "on" if bg_image.show_background_image else "off"
            self.report({'INFO'}, f"Safe area background image turned {status}.")
        else:
            self.report({'ERROR'}, "No background images found on the active camera.")

        return {'FINISHED'}


#================================================== PLAYBLAST ============================================
class VIEW3D_OT_Playblast(bpy.types.Operator):
    """Playblast the viewport with predefined settings"""
    bl_idname = "view3d.playblast"
    bl_label = "Viewport Playblast"

    def switch_workspace(self, workspace_name):
        """Pindah ke workspace yang ditentukan"""
        if workspace_name in bpy.data.workspaces:
            bpy.context.window.workspace = bpy.data.workspaces[workspace_name]
            print(f"Berpindah ke workspace: {workspace_name}")
        else:
            self.report({'WARNING'}, f"Workspace '{workspace_name}' tidak ditemukan! Silakan buat secara manual.")
    
    def execute(self, context):
        scene = context.scene
        
        # Simpan nilai asli start dan end frame
        original_start_frame = scene.frame_start
        original_end_frame = scene.frame_end
        
        # Jika checkbox dicentang, gunakan frame yang diatur
        if scene.use_custom_frame_range:
            scene.frame_start = scene.custom_start_frame
            scene.frame_end = scene.custom_end_frame
        
        self.switch_workspace("Animation")

        output_path = scene.playblast_output_path
        file_name = scene.playblast_file_name
        resolution_x = scene.playblast_resolution_x
        resolution_y = scene.playblast_resolution_y

        if not output_path:
            self.report({'ERROR'}, "Output path is not set. Please specify it in the Scene settings.")
            return {'CANCELLED'}
        if not file_name:
            self.report({'ERROR'}, "File name is not set. Please specify it in the Scene settings.")
            return {'CANCELLED'}
        if resolution_x <= 0 or resolution_y <= 0:
            self.report({'ERROR'}, "Invalid resolution values. Please set both width and height greater than 0.")
            return {'CANCELLED'}

        camera = scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera found in the scene. Please add and set a camera.")
            return {'CANCELLED'}

        # Atur overlay viewport
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_overlays = True
                        space.overlay.show_bones = False
                        space.overlay.show_object_origins = False
                        space.overlay.show_motion_paths = False
                        space.overlay.show_outline_selected = False
                        space.overlay.show_relationship_lines = False
                        space.overlay.show_extras = False
                        space.show_gizmo = False
                        space.overlay.show_viewer_attribute = False
                        space.show_reconstruction = False
                        space.overlay.show_annotation = False
                        space.overlay.show_cursor = False
                        space.overlay.show_text = False
                        space.region_3d.view_perspective = 'CAMERA'

        # Nonaktifkan ekstensi file otomatis
        scene.render.use_file_extension = False

        # Tentukan path output
        full_output_path = os.path.join(bpy.path.abspath(output_path), f"{file_name}.mp4")
        render = scene.render
        render.filepath = full_output_path
        render.resolution_x = resolution_x
        render.resolution_y = resolution_y
        render.image_settings.file_format = 'FFMPEG'
        render.ffmpeg.format = 'QUICKTIME'
        render.ffmpeg.audio_codec = 'MP3'

        # Render playblast
        bpy.ops.render.opengl(animation=True)

        # Kembalikan nilai start dan end frame ke aslinya setelah playblast selesai
        scene.frame_start = original_start_frame
        scene.frame_end = original_end_frame
        
        # Buka file yang telah dirender
        try:
            if os.path.exists(full_output_path):
                if os.name == 'nt':  # Windows
                    os.startfile(full_output_path)
                elif os.name == 'posix':  # macOS/Linux
                    subprocess.call(('xdg-open', full_output_path))
                else:
                    self.report({'WARNING'}, "Could not determine OS to open the video file.")
            else:
                self.report({'ERROR'}, f"Rendered file not found at {full_output_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open the video file: {e}")
        
        self.report({'INFO'}, f"Playblast saved to {full_output_path}")
        

        
        return {'FINISHED'}

#============================================== Tombol Panel =============================================
class VIEW3D_PT_PlayblastPanel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport"""
    bl_label = "Playblast HUD"
    bl_idname = "RAHA_PT_Tools_playblast"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'    
    bl_ui_units_x = 10

    def draw(self, context):
        layout = self.layout
        scene = context.scene
#======================  TOMBOL HUD ====================================================================        
        layout.label(text="HUD ===========") 
        # Input for Scene Name
        layout.prop(scene, "name", text="Scene Name")

        # Input for Animator Name
        layout.prop(scene.render, "stamp_note_text", text="Animator Name")

        # Activate HUD Button
        layout.operator("raha.activate_hud", text="Activate HUD")
        
        # Toggle Safe Area Button
        layout.operator("view3d.toggle_safe_area", text="Toggle Safe Area")        
#======================  TOMBOL PB ====================================================================       
        layout = self.layout
        scene = context.scene
        layout.label(text="Playblast ===========")  
        layout.prop(scene, "playblast_output_path", text="Output Path")
        layout.prop(scene, "playblast_file_name", text="File Name")
        layout.prop(scene, "playblast_resolution_x", text="Resolution X")
        layout.prop(scene, "playblast_resolution_y", text="Resolution Y")
        
        layout.separator()
        
        layout.prop(scene, "use_custom_frame_range", text="Use Custom Frame Range")
        if scene.use_custom_frame_range:
            layout.prop(scene, "custom_start_frame", text="Start Frame")
            layout.prop(scene, "custom_end_frame", text="End Frame")
        
        layout.separator()
        layout.operator("view3d.playblast", text="PLAYBLAST")
        layout.separator()
        

classes = [
    VIEW3D_OT_Playblast,
    VIEW3D_PT_PlayblastPanel,
    RAHA_OT_ActivateHUD,
    VIEW3D_OT_ToggleSafeArea    
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.playblast_output_path = bpy.props.StringProperty(name="Output Path", subtype='DIR_PATH')
    bpy.types.Scene.playblast_file_name = bpy.props.StringProperty(name="File Name")
    bpy.types.Scene.playblast_resolution_x = bpy.props.IntProperty(name="Resolution X", default=1920)
    bpy.types.Scene.playblast_resolution_y = bpy.props.IntProperty(name="Resolution Y", default=1080)
    bpy.types.Scene.use_custom_frame_range = bpy.props.BoolProperty(name="Use Custom Frame Range", default=False)
    bpy.types.Scene.custom_start_frame = bpy.props.IntProperty(name="Custom Start Frame", default=1)
    bpy.types.Scene.custom_end_frame = bpy.props.IntProperty(name="Custom End Frame", default=250)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.playblast_output_path
    del bpy.types.Scene.playblast_file_name
    del bpy.types.Scene.playblast_resolution_x
    del bpy.types.Scene.playblast_resolution_y
    del bpy.types.Scene.use_custom_frame_range
    del bpy.types.Scene.custom_start_frame
    del bpy.types.Scene.custom_end_frame

    
if __name__ == "__main__":
    register()
