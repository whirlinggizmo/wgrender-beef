// wgrender's stress scene (wgrender-c tools/bench/stress.c), in Beef: N entities updated
// every frame, a steady churn of them dying and being replaced, and a screenful of
// formatted text. It follows the C's spec line for line, so every language does the
// same work, and it is written the way Beef naturally would be: an entity is a class
// instance, and a replaced one is deleted, explicitly, and a new one allocated. Text is
// formatted with libc's snprintf, as the simple example does and for the same reason:
// Beef's own formatting links its NumberFormatter and culture data (see its build).
using System;
using wgr;
using static wgr.Wgr;

namespace stress;

class Entity
{
	public float x, y, z, vx, vy, vz, angle, spin, life;
	public WgrHandle sprite;
}

class Program
{
#if BF_PLATFORM_WASM
	const char8* ASSET_BASE  = "/assets";
#else
	const char8* ASSET_BASE  = "assets";
#endif
	const char8* SPRITE_PATH = "sprites/logo/wg-logo-bw-alpha.png";
	const int32 DEFAULT_N = 2000;
	const float STEP = 1.0f / 60.0f;
	const float BOX = 10.0f;
	const int32 TEXT_LINES = 48;

	static int32 n;
	static uint32 rng;
	static Entity[] entities;
	static WgrHandle texture;
	static WgrHandle scene;
	static WgrColor background;

	[CLink] static extern int32 snprintf(char8* buffer, int size, char8* format, ...);
	[CLink] static extern int32 atoi(char8* text);

	// xorshift32, as the spec gives it (logical shifts: rng is unsigned)
	static float Rnd()
	{
		uint32 x = rng;
		x ^= x << 13;
		x ^= x >> 17;
		x ^= x << 5;
		rng = x;
		return (float)(x >> 8) / 16777216.0f;
	}

	static Entity Spawn()
	{
		Entity e = new Entity();
		e.x = (Rnd() * 2 - 1) * BOX / 2;
		e.y = 1 + Rnd() * 4;
		e.z = (Rnd() * 2 - 1) * BOX / 2;
		e.vx = (Rnd() * 2 - 1) * 4;
		e.vy = 4 + Rnd() * 6;
		e.vz = (Rnd() * 2 - 1) * 4;
		e.spin = (Rnd() * 2 - 1) * 3;
		e.life = 2 + Rnd() * 4;
		e.angle = 0;
		e.sprite = wgr_sprite3d_create(texture);
		wgr_sprite3d_set_facing(e.sprite, .Free);
		wgr_scene_add(scene, e.sprite, 0);
		return e;
	}

	static void Update(int i)
	{
		Entity e = entities[i];
		e.vy -= 9.8f * STEP;
		e.x += e.vx * STEP;
		e.y += e.vy * STEP;
		e.z += e.vz * STEP;
		if (e.y < 0)
		{
			e.y = 0;
			e.vy = -e.vy * 0.8f;
		}
		if (Math.Abs(e.x) > BOX)
		{
			e.x = e.x > 0 ? BOX : -BOX;
			e.vx = -e.vx;
		}
		if (Math.Abs(e.z) > BOX)
		{
			e.z = e.z > 0 ? BOX : -BOX;
			e.vz = -e.vz;
		}
		e.angle += e.spin * STEP;
		e.life -= STEP;
		wgr_sprite3d_set_transform(e.sprite, e.x, e.y, e.z, 0, e.angle, 0, 0.5f, 0.5f, 0.5f);
		if (e.life <= 0)
		{
			wgr_sprite3d_destroy(e.sprite);
			delete e;
			entities[i] = Spawn();
		}
	}

	static void OnTextureReady(char8* path, void* user)
	{
		texture = wgr_texture_create(path);
		entities = new Entity[n];
		for (int i < n)
			entities[i] = Spawn();
	}

	static void OnFailed(char8* path, void* user)
	{
		wgr_logger_message(.Error, "failed to import asset: %s", path);
	}

	static void OnInit(void* userData)
	{
		wgr_asset_set_host(ASSET_BASE);
		wgr_logger_set_level(.Warn);
		wgr_set_target_fps(60);
		rng = 2463534242;

		WgrHandle camera = wgr_camera3d_create(.Perspective);
		wgr_camera3d_set_view(camera, 0, 14, 30, 0, 3, 0, 0, 1, 0);
		scene = wgr_scene_create();
		wgr_scene_set_active_camera(scene, camera);
		background = wgr_color_rgba(245, 245, 245, 255);

		WgrHandle task = wgr_asset_ensure_async(SPRITE_PATH, null, ASSET_NONE);
		if (wgr_asset_add_task(task, => OnTextureReady, => OnFailed, null) != .Ok)
			OnFailed(SPRITE_PATH, null);
	}

	static void DrawText()
	{
		char8[128] line = ?;
		snprintf(&line[0], line.Count, "stress: %d entities", n);
		wgr_text_draw(&line[0], 10, 10, 16, COLOR_BLACK);
		if (entities == null)
			return;
		for (int32 i = 0; i < TEXT_LINES && i < n; i++)
		{
			Entity e = entities[i];
			snprintf(&line[0], line.Count, "e%d: %.2f %.2f %.2f life %.2f", i, (double)e.x, (double)e.y,
				(double)e.z, (double)e.life);
			wgr_text_draw(&line[0], 10, 34 + 18 * i, 16, COLOR_BLACK);
		}
	}

	static void OnFrame(float dt, float tickFraction, void* userData)
	{
		if (entities != null)
		{
			for (int i < n)
				Update(i);
		}
		wgr_render_begin_frame();
		wgr_render_clear_background(background);
		wgr_scene_draw(scene);
		DrawText();
		wgr_render_end_frame();
	}

	// ?n= in the page's URL on the web, the first argument on desktop
	static int32 EntityCount(String[] args)
	{
		int32 given = 0;
#if BF_PLATFORM_WASM
		given = emscripten_run_script_int("+(new URLSearchParams(location.search).get('n')) || 0");
#else
		if (args.Count > 0)
			given = atoi(args[0].CStr()); // as the C does; int32.Parse's Result trips BeefBuild 0.43.6 here
#endif
		return given > 0 ? given : DEFAULT_N;
	}

	public static int Main(String[] args)
	{
		n = EntityCount(args);
		wgr_init_values(1024, 1280, "stress (wgrender, Beef)", 0);
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
	[CLink] static extern int32 emscripten_run_script_int(char8* script);
#endif
}
