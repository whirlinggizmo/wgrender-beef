// wgrender simple example in Beef — a port of wgrender's examples/simple.c (itself a
// port of librl's c-simple), with the same scene and behavior.
//
// Scene: an animated model, a bobbing 3D sprite, looping music, two TTF fonts,
// a centered message that reports what the mouse is over (scene picking), and a
// debug overlay with timers, mouse state and the platform name.
//
// Assets are LOGICAL paths resolved against ASSET_BASE: on desktop ./assets (a
// symlink to wgrender's examples/assets, relative to the run cwd, so run from the
// project directory); on the web the served /assets (wgrender's tools/serve.py
// mounts examples/assets there).
using System;
using wgr;
using static wgr.Wgr;

namespace simple;

class Program
{
#if BF_PLATFORM_WASM
	const char8* ASSET_BASE       = "/assets";
#else
	const char8* ASSET_BASE       = "assets";
#endif
	const char8* DEBUG_FONT_PATH  = "fonts/JetBrainsMono/JetBrainsMono-Regular.ttf";
	const char8* KOMIKA_FONT_PATH = "fonts/Komika/KOMIKAH_.ttf";
	const char8* MODEL_PATH       = "models/gumshoe/gumshoe.glb";
	const char8* SPRITE_PATH      = "sprites/logo/wg-logo-bw-alpha.png";
	const char8* BGM_PATH         = "music/ethernight_club.mp3";

	const int32 SCREEN_WIDTH = 1024;
	const int32 SCREEN_HEIGHT = 1280;
	const int32 DEBUG_FONT_SIZE = 18;
	const int32 KOMIKA_FONT_SIZE = 24;

	const float SPRITE_Y_OFFSET = 3.0f;
	const float BOB_SPEED = 1.0f;
	const float BOB_HEIGHT = 1.5f;

	static float elapsed;
	static float countdownTimer;
	static WgrHandle debugFont;
	static WgrColor greyAlpha;
	static WgrHandle komikaFont;
	static WgrHandle sprite;
	static WgrHandle model;
	static WgrHandle bgm;
	static WgrHandle camera;
	static WgrHandle scene;
	static WgrColor backgroundColor;
	static String message = new .() ~ delete _;
	static String platformText = new .() ~ delete _;

	// --- asset callbacks: path is local and ready; create the resource, then the object ---

	static void OnBgmReady(char8* path, void* user)
	{
		WgrHandle audio = wgr_audio_create(path);
		bgm = wgr_sound_create(audio);
		wgr_audio_release(audio); // the sound holds its own reference
		wgr_sound_set_loop(bgm, true);
		wgr_sound_play(bgm);
	}

	static void OnModelReady(char8* path, void* user)
	{
		WgrHandle mesh = wgr_mesh_create(path);
		model = wgr_model_create(mesh);
		wgr_mesh_release(mesh); // the model holds its own reference
		wgr_model_set_animation(model, 1);
		wgr_model_set_animation_speed(model, 1.0f);
		wgr_model_set_animation_loop(model, true);
		wgr_model_set_transform(model, 0, 0, 0, 0, 0, 0, 1, 1, 1);
		wgr_model_set_tint(model, COLOR_RAYWHITE);
		wgr_scene_add(scene, model, 0);
	}

	static void OnSpriteReady(char8* path, void* user)
	{
		WgrHandle texture = wgr_texture_create(path);
		sprite = wgr_sprite3d_create(texture);
		wgr_texture_release(texture); // the sprite holds its own reference
		wgr_sprite3d_set_facing(sprite, .Free); // librl's default: oriented by its rotation
		wgr_sprite3d_set_transform(sprite, 0, SPRITE_Y_OFFSET, 0, 0, 0, 0, 1, 1, 1);
		wgr_sprite3d_set_tint(sprite, COLOR_RAYWHITE);
		wgr_scene_add(scene, sprite, 0);
	}

	// Fonts are sized per draw call in wgrender, so one font handle serves any size.
	static void OnDebugFontReady(char8* path, void* user)
	{
		debugFont = wgr_font_create(path);
	}

	static void OnKomikaFontReady(char8* path, void* user)
	{
		komikaFont = wgr_font_create(path);
	}

	static void OnFailed(char8* path, void* user)
	{
		wgr_logger_message(.Error, "failed to import asset: %s", path);
	}

	static void Load(char8* path, AssetCallbackFn onReady)
	{
		WgrHandle task = wgr_asset_ensure_async(path, null, ASSET_NONE);
		if (wgr_asset_add_task(task, onReady, => OnFailed, null) != .Ok)
			OnFailed(path, null);
	}

	// --- lifecycle ---

	static void OnInit(void* userData)
	{
		wgr_asset_set_host(ASSET_BASE);
		wgr_logger_set_level(.Warn);
		wgr_set_target_fps(60);

		countdownTimer = 30.0f;
		message.Set("Hello from wgrender simple (Beef)!");
		platformText.Set(scope $"Platform: {StringView(wgr_get_platform())}");

		camera = wgr_camera3d_create(.Perspective); // default fov: pi/4 (45 degrees)
		wgr_camera3d_set_view(camera, 12, 12, 12, 0, 1, 0, 0, 1, 0);
		scene = wgr_scene_create();
		wgr_scene_set_active_camera(scene, camera);

		// same lighting as librl's c-simple: a directional light plus ambient 0.25
		WgrHandle sun = wgr_light_create(.Directional);
		wgr_light_set_direction(sun, -0.6f, -1.0f, -0.5f);
		wgr_light_set_intensity(sun, 3.0f);
		wgr_scene_add(scene, sun, 0);
		wgr_scene_set_ambient(scene, COLOR_WHITE, 0.25f);
		backgroundColor = wgr_color_rgba(245, 245, 245, 255);
		greyAlpha = wgr_color_rgba(0, 0, 0, 128);

		Load(BGM_PATH, => OnBgmReady);
		Load(MODEL_PATH, => OnModelReady);
		Load(SPRITE_PATH, => OnSpriteReady);
		Load(DEBUG_FONT_PATH, => OnDebugFontReady);
		Load(KOMIKA_FONT_PATH, => OnKomikaFontReady);
	}

	static void Update(float dt)
	{
		elapsed += dt;
		countdownTimer -= dt;

		if (model != 0)
			wgr_model_animate(model, dt);
		if (sprite != 0)
		{
			float y = Math.Sin(elapsed * BOB_SPEED) * BOB_HEIGHT + SPRITE_Y_OFFSET;
			wgr_sprite3d_set_transform(sprite, 0, y, 0, 0, 0, 0, 1, 1, 1);
		}
	}

	static void UpdatePickMessage(WgrMouseState mouse)
	{
		WgrPickResult pick = wgr_scene_pick(scene, 0, (float)mouse.x, (float)mouse.y);
		StringView what = !pick.hit              ? default
						  : pick.handle == model  ? "Model"
						  : pick.handle == sprite ? "Sprite"
												  : default;
		if (what.IsNull)
		{
			message.Set("Nothing picked!");
			return;
		}
		message.Clear();
		message.AppendF("{} pick: Mouse position (mouse.x:{}, mouse.y:{}) pick result y: {:0.000000}",
			what, mouse.x, mouse.y, pick.point_world.y);
	}

	// Draw with the TTF font once it's loaded, the built-in font until then.
	static void DrawText(WgrHandle font, StringView text, float x, float y, int32 size, WgrColor color)
	{
		if (font != 0)
			wgr_text_draw_ex(font, text.ToScopeCStr!(), x, y, (float)size, color);
		else
			wgr_text_draw(text.ToScopeCStr!(), (int32)x, (int32)y, size, color);
	}

	static void DrawCenteredMessage()
	{
		Vec2 screen = wgr_window_get_screen_size();
		Vec2 size = komikaFont != 0
			? wgr_text_measure_ex(komikaFont, message, (float)KOMIKA_FONT_SIZE)
			: .() { x = (float)wgr_text_measure(message, KOMIKA_FONT_SIZE), y = (float)KOMIKA_FONT_SIZE };
		DrawText(komikaFont, message, (screen.x - size.x) / 2.0f,
			(screen.y - size.y) / 2.0f, KOMIKA_FONT_SIZE, COLOR_BLUE);
	}

	static void DrawOverlay(WgrMouseState mouse)
	{
		DrawText(debugFont, scope $"Remaining: {countdownTimer:0.00}", 10, 36, DEBUG_FONT_SIZE, COLOR_BLACK);
		DrawText(debugFont, scope $"Elapsed: {elapsed:0.00}", 10, 56, DEBUG_FONT_SIZE, COLOR_BLACK);
		DrawText(debugFont, scope $"Mouse: ({mouse.x}, {mouse.y}) w:{mouse.wheel:0.0} b:[{mouse.left}, {mouse.right}, {mouse.middle}]",
			10, 76, DEBUG_FONT_SIZE, COLOR_BLACK);
		DrawText(debugFont, platformText, 10, 96, DEBUG_FONT_SIZE, COLOR_BLACK);

		wgr_text_draw_fps_ex(debugFont, 10, 10, DEBUG_FONT_SIZE, greyAlpha);
	}

	static void OnFrame(float dt, float tickFraction, void* userData)
	{
		WgrMouseState mouse = wgr_input_get_mouse_state();

#if !BF_PLATFORM_WASM
		// Escape quits on desktop; a web page has nothing to quit to.
		if (wgr_input_get_key(.Escape) == .Pressed)
			wgr_request_quit();
#endif

		Update(dt);
		UpdatePickMessage(mouse);

		wgr_render_begin();
		wgr_render_clear_background(backgroundColor);
		wgr_scene_draw(scene);
		DrawCenteredMessage();
		DrawOverlay(mouse);
		wgr_render_end();
	}

	public static int Main(String[] args)
	{
		wgr_init_values(SCREEN_WIDTH, SCREEN_HEIGHT, "simple (wgrender, Beef)", WINDOW_FLAG_MSAA_4X_HINT);
		wgr_set_init(=> OnInit, null);
		wgr_set_frame(=> OnFrame, null);
		int32 result = wgr_run();
#if BF_PLATFORM_WASM
		// On the web wgr_run returns at once and the browser drives frames. Leave
		// without returning, so Beef's shutdown doesn't run static destructors
		// under the frame callbacks.
		emscripten_exit_with_live_runtime();
#endif
		return result;
	}

#if BF_PLATFORM_WASM
	[CLink] static extern void emscripten_exit_with_live_runtime();
#endif
}
