import bpy
import os
from bpy.props import StringProperty, CollectionProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList


#=================================================================================
# Property Group untuk menyimpan informasi video 
class VideoItem(PropertyGroup):
    name: StringProperty(name="Name")
    path: StringProperty(name="Path")

#============================================== refresh list ======================
class WM_OT_RefreshList(bpy.types.Operator):
    bl_idname = "wm.refresh_list"
    bl_label = "Refresh List"
    bl_description = "Refresh the list of videos in the selected folder"
    
    def execute(self, context):
        if context.scene.video_folder:
            bpy.ops.wm.select_folder(directory=context.scene.video_folder)
            self.report({'INFO'}, "List refreshed.")
        else:
            self.report({'ERROR'}, "No folder selected.")
        return {'FINISHED'}    

# Operator untuk memilih folder
class WM_OT_SelectFolder(bpy.types.Operator):
    bl_idname = "wm.select_folder"
    bl_label = "Select Folder"
    bl_description = "Select a folder to browse videos"
    
    directory: StringProperty(subtype='DIR_PATH')
    
    def execute(self, context):
        context.scene.video_folder = self.directory
        context.scene.video_list.clear()
        
        for file in os.listdir(self.directory):
            if file.endswith((".mp4", ".avi", ".mkv", ".mov")):
                item = context.scene.video_list.add()
                item.name = file
                item.path = os.path.join(self.directory, file)
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Operator untuk memutar video
class WM_OT_PlayVideo(bpy.types.Operator):
    bl_idname = "wm.play_video"
    bl_label = "Play Video"
    bl_description = "Play selected video using default video player"
    
    def execute(self, context):
        selected_video = context.scene.video_list[context.scene.video_index]
        video_path = selected_video.path
        
        if os.name == 'nt':
            os.startfile(video_path)
        else:
            self.report({'ERROR'}, "This addon only works on Windows.")
        
        return {'FINISHED'}
    
# Operator untuk mengimpor script animasi
class WM_OT_ImportAnimation(bpy.types.Operator):
    bl_idname = "wm.import_animation"
    bl_label = "Import Animation"
    bl_description = "Import animation data from selected video's script"
    
    def execute(self, context):
        selected_video = context.scene.video_list[context.scene.video_index]
        video_name = selected_video.name
        directory = context.scene.video_folder
        
        # Path ke folder ANIM_DATA
        anim_data_dir = os.path.join(directory, "ANIM_DATA")
        
        if not os.path.exists(anim_data_dir):
            self.report({'ERROR'}, f"Folder ANIM_DATA tidak ditemukan di: {directory}")
            return {'CANCELLED'}
        
        # Path ke file script
        script_filepath = os.path.join(anim_data_dir, f"{os.path.splitext(video_name)[0]}.py")
        
        if not os.path.exists(script_filepath):
            self.report({'ERROR'}, f"File script {os.path.basename(script_filepath)} tidak ditemukan di: {anim_data_dir}")
            return {'CANCELLED'}
        
        # Baca dan eksekusi script
        try:
            with open(script_filepath, 'r') as file:
                exec(file.read())
            self.report({'INFO'}, f"Data keyframe dari {script_filepath} berhasil diimpor.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Terjadi error saat mengimpor script: {e}")
            return {'CANCELLED'}
    

# Operator untuk menghapus video
class WM_OT_DeleteVideo(bpy.types.Operator):
    bl_idname = "wm.delete_video"
    bl_label = "Delete Video"
    bl_description = "Delete the selected video and its corresponding script"
    
    def execute(self, context):
        selected_video = context.scene.video_list[context.scene.video_index]
        video_name = selected_video.name
        video_path = selected_video.path
        directory = context.scene.video_folder
        
        # Path ke folder ANIM_DATA
        anim_data_dir = os.path.join(directory, "ANIM_DATA")
        script_filepath = os.path.join(anim_data_dir, f"{os.path.splitext(video_name)[0]}.py")
        
        # Hapus script jika ada
        if os.path.exists(script_filepath):
            try:
                os.remove(script_filepath)
                self.report({'INFO'}, f"Script {os.path.basename(script_filepath)} deleted.")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to delete script: {e}")
                return {'CANCELLED'}
        
        # Hapus video
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
                self.report({'INFO'}, f"Video {video_name} deleted.")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to delete video: {e}")
                return {'CANCELLED'}
        
        # Refresh daftar video
        bpy.ops.wm.refresh_list()
        
        return {'FINISHED'}

# UIList untuk menampilkan daftar video
class VIDEO_UL_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)
                      
# Panel untuk UI
class VIDEO_PT_Browser(bpy.types.Panel):
    bl_label = "Import Animation"
    bl_idname = "VIDEO_PT_Browser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.operator("wm.select_folder", text="Select Folder")
        row.operator("wm.refresh_list", text="", icon='FILE_REFRESH')     
        
        if scene.video_folder:
            layout.label(text=f"Selected Folder: {scene.video_folder}")
        
        if scene.video_list:
            layout.template_list("VIDEO_UL_List", "", scene, "video_list", scene, "video_index")
            
            if scene.video_index >= 0 and scene.video_index < len(scene.video_list):
                row = layout.row()
                row.operator("wm.play_video", text="Preview")
                row.operator("wm.import_animation", text="Import Animation")
                row.operator("wm.delete_video", text="Delete", icon='TRASH')

# Register dan Unregister
classes = ( 
    VideoItem,
    WM_OT_SelectFolder,
    WM_OT_PlayVideo,
    WM_OT_ImportAnimation,
    WM_OT_DeleteVideo,
    VIDEO_UL_List,
    VIDEO_PT_Browser,
    WM_OT_RefreshList
)

def register():
    print("Import ANM Registered")  
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.video_folder = StringProperty(name="Video Folder")
    bpy.types.Scene.video_list = CollectionProperty(type=VideoItem)
    bpy.types.Scene.video_index = bpy.props.IntProperty(name="Index", default=0)

def unregister():
    print("Import ANM Unregistered")    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.video_folder
    del bpy.types.Scene.video_list
    del bpy.types.Scene.video_index

if __name__ == "__main__":
    register()
