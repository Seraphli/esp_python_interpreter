from appdirs import *
import codecs
import json
import asyncio
import socketio
import uuid

APP_NAME = "electron-spirit"
PLUGIN_NAME = "ES Python"
SHORT_NAME = "py"
PLUGIN_SETTING = "plugin.setting.json"


class PluginApi(socketio.AsyncClientNamespace):
    def __init__(self, parent):
        super().__init__()
        self.elem_count = 0
        self.parent = parent

    def on_connect(self):
        print("Connected")

    def on_disconnect(self):
        print("Disconnected")

    def on_echo(self, data):
        print("Echo:", data)

    def on_register_topic(self, data):
        print("Register topic:", data)

    def on_add_input_hook(self, data):
        print("Add input hook:", data)

    def on_del_input_hook(self, data):
        print("Del input hook:", data)

    def on_insert_css(self, data):
        print("Insert css:", data)

    def on_remove_css(self, data):
        print("Remove css:", data)

    def on_update_elem(self, data):
        print("Update elem:", data)
        self.elem_count += 1

    def on_remove_elem(self, data):
        print("Remove elem:", data)
        self.elem_count -= 1

    def on_show_view(self, data):
        print("Show view:", data)

    def on_hide_view(self, data):
        print("Hide view:", data)

    def on_exec_js_in_elem(self, data):
        print("Exec js in elem:", data)

    def on_notify(self, data):
        print("Notify:", data)

    def on_update_bound(self, key, _type, bound):
        print("Update bound:", key, _type, bound)

    async def on_process_content(self, content):
        print("Process content:", content)
        await self.parent.calc(content)

    def on_mode_flag(self, lock_flag, move_flag, dev_flag):
        print("Mode flag:", lock_flag, move_flag, dev_flag)


class Plugin(object):
    def __init__(self) -> None:
        self.load_config()
        self.locals = {}
        self.globals = {}
        self.api = PluginApi(self)

    async def calc(self, content):
        try:
            res = eval(content, self.globals, self.locals)
            await sio.emit(
                "notify",
                data=(
                    self.ctx,
                    {
                        "text": res if res is not None else "",
                        "title": PLUGIN_NAME,
                        "duration": self.cfg["duration"],
                    },
                ),
            )
            print(res)
        except SyntaxError:
            try:
                res = exec(content, self.globals, self.locals)
                await sio.emit(
                    "notify",
                    data=(
                        self.ctx,
                        {
                            "text": res if res is not None else "",
                            "title": PLUGIN_NAME,
                            "duration": self.cfg["duration"],
                        },
                    ),
                )
                print(res)
            except Exception as e:
                await sio.emit(
                    "notify",
                    data=(
                        self.ctx,
                        {
                            "text": str(e),
                            "title": PLUGIN_NAME,
                            "duration": self.cfg["duration"],
                            "type": "error",
                        },
                    ),
                )
                print(e)
        except Exception as e:
            await sio.emit(
                "notify",
                data=(
                    self.ctx,
                    {
                        "text": str(e),
                        "title": PLUGIN_NAME,
                        "duration": self.cfg["duration"],
                        "type": "error",
                    },
                ),
            )
            print(e)

    def load_config(self):
        path = user_data_dir(APP_NAME, False, roaming=True)
        with codecs.open(path + "/api.json") as f:
            config = json.load(f)
        self.port = config["apiPort"]
        try:
            with codecs.open(PLUGIN_SETTING) as f:
                self.cfg = json.load(f)
        except:
            self.cfg = {"duration": -1}
        self.save_cfg()

    def save_cfg(self):
        with codecs.open(PLUGIN_SETTING, "w") as f:
            json.dump(self.cfg, f)

    async def register(self):
        # Create a context for registering plugins
        # You can either use sample password or use complex password
        # You can also register multiple topic
        ctx = {"topic": SHORT_NAME, "pwd": str(uuid.uuid4())}
        await sio.emit("register_topic", ctx)
        self.ctx = ctx

    async def wait_for_elem(self):
        while self.api.elem_count < 2:
            await asyncio.sleep(0.1)

    async def test_case(self):
        await sio.emit("add_input_hook", data=(self.ctx, "py"))
        await sio.emit(
            "notify",
            data=(
                self.ctx,
                {"text": "Python Interpreter started.", "title": PLUGIN_NAME},
            ),
        )

    async def loop(self):
        await sio.connect(f"http://localhost:{self.port}")
        await self.register()
        await self.test_case()
        await sio.wait()


if __name__ == "__main__":
    # asyncio
    sio = socketio.AsyncClient()
    p = Plugin()
    sio.register_namespace(p.api)
    asyncio.run(p.loop())