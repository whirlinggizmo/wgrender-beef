using System;

namespace wgr;

// Hand-written bindings for the slice of wgrender (include/wgr*.h) that the simple
// example uses. Handles are wgr_handle_t (unsigned int); colors are wgr_color_t,
// packed 0xRRGGBBAA values.

typealias WgrHandle = uint32;
typealias WgrColor = uint32;

[CRepr]
struct Vec2
{
	public float x;
	public float y;
}

[CRepr]
struct Vec3
{
	public float x;
	public float y;
	public float z;
}

[CRepr]
struct WgrMouseState
{
	public int32 x;
	public int32 y;
	public float wheel;
	public float wheel_x;
	public int32 left;
	public int32 right;
	public int32 middle;
	public int32[3] buttons;
	public int32 dx;
	public int32 dy;
}

[CRepr]
struct WgrPickResult
{
	public bool hit;
	public WgrHandle handle;
	public float distance;
	public Vec3 point_local;
	public Vec3 point_world;
	public Vec3 normal_local;
	public Vec3 normal_world;
}

enum WgrButtonState : int32
{
	Up = 0,
	Pressed = 1,
	Down = 2,
	Released = 3,
}

enum WgrKey : int32
{
	Escape = 256,
}

enum WgrLogLevel : int32
{
	Trace = 0,
	Debug = 1,
	Info = 2,
	Warn = 3,
	Error = 4,
	Fatal = 5,
}

enum WgrCamera3DProjection : int32
{
	Perspective = 0,
}

enum WgrLightType : int32
{
	Directional = 0,
}

enum WgrSprite3DFacing : int32
{
	Free = 3,
}

enum WgrAssetAddTaskResult : int32
{
	Ok = 0,
}

static class Wgr
{
	public const uint32 WINDOW_FLAG_MSAA_4X_HINT = 0x00000020;
	public const uint32 ASSET_NONE = 0;

	public const WgrColor COLOR_BLUE     = 0x0079F1FF;
	public const WgrColor COLOR_WHITE    = 0xFFFFFFFF;
	public const WgrColor COLOR_BLACK    = 0x000000FF;
	public const WgrColor COLOR_RAYWHITE = 0xF5F5F5FF;

	public typealias TickFn = function void(float dt, void* userData);
	public typealias FrameFn = function void(float dt, float tickFraction, void* userData);
	public typealias LifecycleFn = function void(void* userData);
	public typealias AssetCallbackFn = function void(char8* path, void* userData);

	// sk.h
	[CLink] public static extern int32 wgr_init_values(int32 width, int32 height, char8* title, uint32 flags);
	[CLink] public static extern void wgr_set_frame(FrameFn fn, void* userData);
	[CLink] public static extern void wgr_set_init(LifecycleFn fn, void* userData);
	[CLink] public static extern int32 wgr_run();
	[CLink] public static extern void wgr_request_quit();
	[CLink] public static extern char8* wgr_get_platform();
	[CLink] public static extern void wgr_set_target_fps(int32 fps);

	// wgr_logger.h
	[CLink] public static extern void wgr_logger_set_level(WgrLogLevel level);
	[CLink] public static extern void wgr_logger_message(WgrLogLevel level, char8* format, ...);

	// wgr_asset.h
	[CLink] public static extern void wgr_asset_set_host(char8* host);
	[CLink] public static extern WgrHandle wgr_asset_ensure_async(char8* path, char8* fetchUrl, uint32 flags);
	[CLink] public static extern WgrAssetAddTaskResult wgr_asset_add_task(WgrHandle task, AssetCallbackFn onSuccess, AssetCallbackFn onFailure, void* userData);

	// wgr_color.h
	[CLink] public static extern WgrColor wgr_color_rgba(int32 r, int32 g, int32 b, int32 a);

	// wgr_audio.h, wgr_sound.h
	[CLink] public static extern WgrHandle wgr_audio_create(char8* path);
	[CLink] public static extern void wgr_audio_release(WgrHandle audio);
	[CLink] public static extern WgrHandle wgr_sound_create(WgrHandle audio);
	[CLink] public static extern bool wgr_sound_set_loop(WgrHandle sound, bool loop);
	[CLink] public static extern bool wgr_sound_play(WgrHandle sound);

	// wgr_model.h
	[CLink] public static extern WgrHandle wgr_mesh_create(char8* path);
	[CLink] public static extern void wgr_mesh_release(WgrHandle mesh);
	[CLink] public static extern WgrHandle wgr_model_create(WgrHandle mesh);
	[CLink] public static extern bool wgr_model_set_animation(WgrHandle model, int32 index);
	[CLink] public static extern bool wgr_model_set_animation_speed(WgrHandle model, float speed);
	[CLink] public static extern bool wgr_model_set_animation_loop(WgrHandle model, bool loop);
	[CLink] public static extern bool wgr_model_set_transform(WgrHandle model, float px, float py, float pz, float rx, float ry, float rz, float sx, float sy, float sz);
	[CLink] public static extern bool wgr_model_set_position(WgrHandle model, float x, float y, float z);
	[CLink] public static extern bool wgr_model_set_rotation(WgrHandle model, float x, float y, float z);
	[CLink] public static extern bool wgr_model_set_scale(WgrHandle model, float x, float y, float z);
	[CLink] public static extern Vec3 wgr_model_get_position(WgrHandle model);
	[CLink] public static extern Vec3 wgr_model_get_rotation(WgrHandle model);
	[CLink] public static extern Vec3 wgr_model_get_scale(WgrHandle model);
	[CLink] public static extern bool wgr_model_set_tint(WgrHandle model, WgrColor color);
	[CLink] public static extern bool wgr_model_animate(WgrHandle model, float dt);

	// wgr_texture.h, wgr_sprite3d.h
	[CLink] public static extern WgrHandle wgr_texture_create(char8* path);
	[CLink] public static extern void wgr_texture_release(WgrHandle texture);
	[CLink] public static extern WgrHandle wgr_sprite3d_create(WgrHandle texture);
	[CLink] public static extern bool wgr_sprite3d_set_facing(WgrHandle sprite, WgrSprite3DFacing facing);
	[CLink] public static extern void wgr_sprite3d_destroy(WgrHandle sprite);
	[CLink] public static extern bool wgr_sprite3d_set_transform(WgrHandle sprite, float px, float py, float pz, float rx, float ry, float rz, float sx, float sy, float sz);
	[CLink] public static extern bool wgr_sprite3d_set_position(WgrHandle sprite, float x, float y, float z);
	[CLink] public static extern bool wgr_sprite3d_set_rotation(WgrHandle sprite, float x, float y, float z);
	[CLink] public static extern bool wgr_sprite3d_set_scale(WgrHandle sprite, float x, float y, float z);
	[CLink] public static extern Vec3 wgr_sprite3d_get_position(WgrHandle sprite);
	[CLink] public static extern Vec3 wgr_sprite3d_get_rotation(WgrHandle sprite);
	[CLink] public static extern Vec3 wgr_sprite3d_get_scale(WgrHandle sprite);
	[CLink] public static extern bool wgr_sprite3d_set_tint(WgrHandle sprite, WgrColor color);

	// wgr_font.h, wgr_text.h
	[CLink] public static extern WgrHandle wgr_font_create(char8* path);
	[CLink] public static extern void wgr_text_draw(char8* text, int32 x, int32 y, int32 size, WgrColor color);
	[CLink] public static extern int32 wgr_text_measure(char8* text, int32 size);
	[CLink] public static extern void wgr_text_draw_ex(WgrHandle font, char8* text, float x, float y, float size, WgrColor color);
	[CLink] public static extern Vec2 wgr_text_measure_ex(WgrHandle font, char8* text, float size);
	[CLink] public static extern void wgr_text_draw_fps_ex(WgrHandle font, float x, float y, float size, WgrColor color);

	// wgr_camera3d.h, wgr_light.h, wgr_scene.h
	[CLink] public static extern WgrHandle wgr_camera3d_create(WgrCamera3DProjection projection);
	[CLink] public static extern bool wgr_camera3d_set_view(WgrHandle camera, float px, float py, float pz, float tx, float ty, float tz, float ux, float uy, float uz);
	[CLink] public static extern WgrHandle wgr_light_create(WgrLightType type);
	[CLink] public static extern bool wgr_light_set_direction(WgrHandle light, float x, float y, float z);
	[CLink] public static extern bool wgr_light_set_intensity(WgrHandle light, float intensity);
	[CLink] public static extern WgrHandle wgr_scene_create();
	[CLink] public static extern bool wgr_scene_add(WgrHandle scene, WgrHandle drawable, int32 layer);
	[CLink] public static extern void wgr_scene_set_active_camera(WgrHandle scene, WgrHandle camera);
	[CLink] public static extern bool wgr_scene_set_ambient(WgrHandle scene, WgrColor color, float intensity);
	[CLink] public static extern void wgr_scene_draw(WgrHandle scene);
	[CLink] public static extern WgrPickResult wgr_scene_pick(WgrHandle scene, WgrHandle camera, float x, float y);

	// wgr_input.h, wgr_window.h, wgr_render.h
	[CLink] public static extern WgrMouseState wgr_input_get_mouse_state();
	[CLink] public static extern WgrButtonState wgr_input_get_key(WgrKey key); // Up for an unknown key
	[CLink] public static extern Vec2 wgr_window_get_screen_size();
	[CLink] public static extern void wgr_render_begin_frame();
	[CLink] public static extern void wgr_render_end_frame();
	[CLink] public static extern void wgr_render_clear_background(WgrColor color);
}
